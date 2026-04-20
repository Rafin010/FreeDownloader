import os
import sys
import uuid
import threading
import time
import re
import random
import logging
import json
from urllib.parse import quote, urlparse
from flask import Flask, render_template, request, jsonify, send_file, make_response, Response
import yt_dlp
import requests as http_requests
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Add parent dir to path for shared infra imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infra.redis_client import get_limiter_storage_uri, cache_get, cache_set, is_redis_available
from infra.progress import get_progress
from infra.proxy_pool import get_proxy, mark_bad as mark_proxy_bad

app = Flask(__name__)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["60 per minute"],
    storage_uri=get_limiter_storage_uri()
)

# ── Logging Setup ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, 'downloads')
COOKIES_FILE = os.path.join(BASE_DIR, 'cookies.txt')
PO_TOKEN_FILE = os.path.join(BASE_DIR, 'po_token.txt')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

FILE_EXPIRY_TIME = 1800  # 30 minutes


# ── Check if curl-cffi is available for browser impersonation ──
_HAS_CURL_CFFI = False
try:
    import curl_cffi  # noqa: F401
    _HAS_CURL_CFFI = True
    logger.info("✅ curl-cffi detected — browser TLS impersonation ENABLED")
except ImportError:
    logger.warning("⚠️  curl-cffi not installed — browser impersonation DISABLED. "
                   "Install with: pip install curl-cffi")


# ── Startup Diagnostics ───────────────────────────────────────
def get_yt_dlp_version():
    """Log the current yt-dlp version for diagnostic purposes."""
    try:
        version = yt_dlp.version.__version__
        logger.info("yt-dlp version: %s", version)
        return version
    except Exception:
        logger.warning("Could not determine yt-dlp version")
        return "unknown"


def validate_yt_cookies():
    """Check if cookies.txt contains real authenticated YouTube cookies.
    Logs a clear warning if not — does NOT crash."""
    if not os.path.exists(COOKIES_FILE):
        logger.warning("⚠️  No cookies.txt found at %s — YouTube may block unauthenticated requests. "
                       "Export cookies from a logged-in browser session for best results.", COOKIES_FILE)
        return False

    try:
        with open(COOKIES_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Check for authenticated session markers
        auth_markers = ['LOGIN_INFO', 'SID', 'SSID', 'HSID', 'APISID', 'SAPISID',
                        '__Secure-1PSID', '__Secure-3PSID']
        found = [m for m in auth_markers if m in content]

        if found:
            logger.info("✅ cookies.txt contains authenticated session cookies: %s", ', '.join(found[:3]))
            return True
        else:
            logger.warning("⚠️  cookies.txt exists but contains NO authenticated session cookies. "
                           "Current cookies are only consent/preference cookies (PREF, SOCS, etc.) "
                           "which do NOT help bypass bot detection. "
                           "Re-export cookies from a LOGGED-IN YouTube session for reliable downloads.")
            return False
    except Exception as e:
        logger.warning("⚠️  Could not read cookies.txt: %s", e)
        return False


def load_po_token():
    """Load PO (Proof of Origin) token if available.
    This token is required for web client extraction on servers since 2025+."""
    if not os.path.exists(PO_TOKEN_FILE):
        logger.info("ℹ️  No po_token.txt found — PO token not configured. "
                    "Generate one with: npx playwright install && node po_token_generator.js")
        return None, None

    try:
        with open(PO_TOKEN_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        # Expected format: visitor_data:po_token  OR  JSON {"visitor_data": "...", "po_token": "..."}
        if content.startswith('{'):
            data = json.loads(content)
            visitor_data = data.get('visitor_data', '')
            po_token = data.get('po_token', '')
        elif ':' in content:
            parts = content.split(':', 1)
            visitor_data = parts[0].strip()
            po_token = parts[1].strip()
        else:
            logger.warning("⚠️  po_token.txt format unrecognized. Expected 'visitor_data:po_token' or JSON.")
            return None, None

        if visitor_data and po_token:
            logger.info("✅ PO token loaded successfully (visitor_data: %s...)", visitor_data[:20])
            return visitor_data, po_token
        else:
            logger.warning("⚠️  po_token.txt exists but is incomplete.")
            return None, None

    except Exception as e:
        logger.warning("⚠️  Could not read po_token.txt: %s", e)
        return None, None


# Run diagnostics at startup
_yt_dlp_version = get_yt_dlp_version()
_has_auth_cookies = validate_yt_cookies()
_visitor_data, _po_token = load_po_token()


# ── YouTube-specific: Multiple extraction strategies ──────────
# Updated 2026-04: Current effective client set for bypassing bot detection.
# Deprecated clients (android, android_vr, ios_embedded) have been removed.
STRATEGIES = [
    # Strategy 0: web_embedded — embedded player, often bypasses bot checks
    {'youtube': {'player_client': ['web_embedded']}},
    # Strategy 1: web_creator — creator studio client, avoids sign-in prompts (2026)
    {'youtube': {'player_client': ['web_creator']}},
    # Strategy 2: mweb — mobile web client, lighter bot detection
    {'youtube': {'player_client': ['mweb']}},
    # Strategy 3: ios — iOS native client, lower bot detection
    {'youtube': {'player_client': ['ios']}},
    # Strategy 4: tv — smart TV client, minimal detection
    {'youtube': {'player_client': ['tv']}},
    # Strategy 5: default — let yt-dlp auto-select the best client
    {},
]

# User-Agent rotation pool — 2026-era browser versions
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/19.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 19_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/19.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0",
]


def build_yt_opts(strategy_idx=0):
    """Build yt-dlp options for YouTube, rotating strategies and User-Agents."""
    idx = strategy_idx % len(STRATEGIES)
    ua_idx = strategy_idx % len(USER_AGENTS)
    ext_args = STRATEGIES[idx]

    headers = {
        "User-Agent": USER_AGENTS[ua_idx],
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Sec-Ch-Ua": '"Chromium";v="131", "Not A(Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
    }

    opts = {
        'quiet': True,
        'no_warnings': True,
        'http_headers': headers,
        'socket_timeout': 30,
        'force_ipv4': True,
        # Rate limiting: sleep between requests to avoid triggering 429
        'sleep_interval': 2,
        'max_sleep_interval': 6,
        'sleep_interval_requests': 1,
        # Retry internal yt-dlp fragment downloads
        'retries': 5,
        'fragment_retries': 5,
        # SSL: prefer verified certs, fallback handled in retry logic
        'nocheckcertificate': False,
    }

    if ext_args:
        opts['extractor_args'] = dict(ext_args)  # copy to avoid mutation

    # PO Token injection — required for web client on servers since 2025+
    if _po_token and _visitor_data:
        if 'extractor_args' not in opts:
            opts['extractor_args'] = {}
        if 'youtube' not in opts['extractor_args']:
            opts['extractor_args']['youtube'] = {}

        opts['extractor_args']['youtube']['po_token'] = [f'web+{_po_token}']
        opts['extractor_args']['youtube']['visitor_data'] = [_visitor_data]

    # Browser TLS impersonation (requires curl-cffi)
    if _HAS_CURL_CFFI:
        opts['impersonate'] = 'chrome'

    # Cookies — use if available
    if os.path.exists(COOKIES_FILE):
        opts['cookiefile'] = COOKIES_FILE

    return opts, len(STRATEGIES)


def _is_unrecoverable_error(error_str):
    """Check if an error is truly unrecoverable and should NOT be retried."""
    unrecoverable = [
        'is not a valid url',
        'private video',
        'video unavailable',
        'this video has been removed',
        'copyright',
        'this video is no longer available',
    ]
    error_lower = error_str.lower()
    return any(pattern in error_lower for pattern in unrecoverable)


# ── Invidious / Piped API Fallback ────────────────────────────
# When ALL yt-dlp strategies fail, try public Invidious instances
# as a zero-dependency backup for metadata extraction.
INVIDIOUS_INSTANCES = [
    "https://vid.puffyan.us",
    "https://inv.nadeko.net",
    "https://invidious.nerdvpn.de",
    "https://invidious.privacyredirect.com",
    "https://iv.ggtyler.dev",
]

PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://pipedapi.r4fo.com",
    "https://pipedapi.adminforge.de",
]


def extract_video_id(url):
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r'(?:youtube\.com/watch\?.*v=|youtu\.be/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        r'youtube\.com/v/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def extract_via_invidious_api(video_url):
    """Fallback: Extract video info via public Invidious/Piped API instances.
    Returns a dict compatible with yt-dlp info_dict format, or None on failure."""
    video_id = extract_video_id(video_url)
    if not video_id:
        logger.warning("Invidious fallback: Could not extract video ID from URL: %s", video_url)
        return None

    # Try Invidious instances first
    for instance in INVIDIOUS_INSTANCES:
        try:
            api_url = f"{instance}/api/v1/videos/{video_id}"
            logger.info("🔄 Trying Invidious fallback: %s", instance)
            resp = http_requests.get(api_url, timeout=15, headers={
                "User-Agent": USER_AGENTS[0],
                "Accept": "application/json",
            })

            if resp.status_code == 200:
                data = resp.json()
                # Build yt-dlp compatible info dict
                formats = []
                for stream in data.get('formatStreams', []) + data.get('adaptiveFormats', []):
                    fmt = {
                        'url': stream.get('url', ''),
                        'ext': stream.get('container', 'mp4'),
                        'height': int(stream.get('resolution', '0p').replace('p', '') or 0),
                        'format_note': stream.get('qualityLabel', ''),
                    }
                    if fmt['url']:
                        formats.append(fmt)

                if formats:
                    info = {
                        'id': video_id,
                        'title': data.get('title', 'YouTube_Video'),
                        'description': data.get('description', ''),
                        'thumbnail': data.get('videoThumbnails', [{}])[0].get('url', '') if data.get('videoThumbnails') else '',
                        'thumbnails': [{'url': t.get('url', '')} for t in data.get('videoThumbnails', [])],
                        'formats': formats,
                        'duration': data.get('lengthSeconds', 0),
                        '_invidious_source': instance,
                    }
                    logger.info("✅ Invidious fallback succeeded via %s", instance)
                    return info

        except Exception as e:
            logger.warning("Invidious instance %s failed: %s", instance, str(e)[:80])
            continue

    # Try Piped instances as secondary fallback
    for instance in PIPED_INSTANCES:
        try:
            api_url = f"{instance}/streams/{video_id}"
            logger.info("🔄 Trying Piped fallback: %s", instance)
            resp = http_requests.get(api_url, timeout=15, headers={
                "User-Agent": USER_AGENTS[1],
                "Accept": "application/json",
            })

            if resp.status_code == 200:
                data = resp.json()
                formats = []
                for stream in data.get('videoStreams', []) + data.get('audioStreams', []):
                    fmt = {
                        'url': stream.get('url', ''),
                        'ext': stream.get('format', 'mp4'),
                        'height': stream.get('height', 0) or 0,
                        'format_note': stream.get('quality', ''),
                    }
                    if fmt['url']:
                        formats.append(fmt)

                if formats:
                    info = {
                        'id': video_id,
                        'title': data.get('title', 'YouTube_Video'),
                        'description': data.get('description', ''),
                        'thumbnail': data.get('thumbnailUrl', ''),
                        'thumbnails': [{'url': data.get('thumbnailUrl', '')}] if data.get('thumbnailUrl') else [],
                        'formats': formats,
                        'duration': data.get('duration', 0),
                        '_piped_source': instance,
                    }
                    logger.info("✅ Piped fallback succeeded via %s", instance)
                    return info

        except Exception as e:
            logger.warning("Piped instance %s failed: %s", instance, str(e)[:80])
            continue

    logger.error("❌ ALL Invidious/Piped fallback instances failed for video: %s", video_id)
    return None


def extract_with_retry(video_url):
    """Try ALL strategies with jittered exponential backoff.
    Falls back to Invidious/Piped API if all yt-dlp strategies fail."""
    _, num_strategies = build_yt_opts(0)
    max_attempts = num_strategies * 2  # Double cycle for resilience
    last_error = None

    for i in range(max_attempts):
        try:
            opts, _ = build_yt_opts(i)
            strategy_name = f"Strategy {i % num_strategies}" + (" (cycle 2)" if i >= num_strategies else "")
            logger.info("YT extract attempt %d/%d [%s] for: %s", i + 1, max_attempts, strategy_name, video_url)

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                logger.info("✅ YT extraction succeeded on attempt %d [%s]", i + 1, strategy_name)
                return info, i

        except Exception as e:
            last_error = e
            error_str = str(e)

            if _is_unrecoverable_error(error_str):
                logger.error("❌ Unrecoverable error (not retrying): %s", error_str[:150])
                raise e

            # Jittered exponential backoff: base * 2^attempt + random jitter
            base_backoff = min(2 * (i + 1), 15)
            jitter = random.uniform(0, 2)
            backoff = base_backoff + jitter
            logger.warning("YT attempt %d failed: %s — backing off %.1fs before next...",
                           i + 1, error_str[:120], backoff)

            if i < max_attempts - 1:
                time.sleep(backoff)
            continue

    # ── Invidious/Piped API Fallback ──────────────────────────
    logger.info("🔄 All yt-dlp strategies exhausted — trying Invidious/Piped API fallback...")
    api_info = extract_via_invidious_api(video_url)
    if api_info:
        logger.info("✅ Fallback API extraction succeeded!")
        return api_info, -1  # -1 signals fallback

    # All attempts exhausted — log detailed diagnostic info
    logger.error("❌ ALL %d YouTube strategies + API fallbacks exhausted for: %s", max_attempts, video_url)
    logger.error("   Last error: %s", str(last_error))
    logger.error("   yt-dlp version: %s | curl-cffi: %s | auth cookies: %s | PO token: %s",
                 _yt_dlp_version, _HAS_CURL_CFFI, _has_auth_cookies, bool(_po_token))
    raise last_error


def download_with_retry(video_url, filepath, res_height):
    """Download video using multiple strategies with jittered exponential backoff."""
    _, num_strategies = build_yt_opts(0)
    max_attempts = num_strategies * 2
    last_error = None

    for i in range(max_attempts):
        try:
            opts, _ = build_yt_opts(i)
            opts['socket_timeout'] = 120  # Longer timeout for downloads
            opts.update({
                'format': f'bestvideo[height<={res_height}]+bestaudio/best[height<={res_height}]/best',
                'merge_output_format': 'mp4',
                'outtmpl': filepath,
            })

            strategy_name = f"Strategy {i % num_strategies}" + (" (cycle 2)" if i >= num_strategies else "")
            logger.info("YT download attempt %d/%d [%s]", i + 1, max_attempts, strategy_name)

            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([video_url])

            if os.path.exists(filepath):
                logger.info("✅ YT download succeeded on attempt %d [%s]", i + 1, strategy_name)
                return True

        except Exception as e:
            last_error = e
            error_str = str(e)

            if _is_unrecoverable_error(error_str):
                raise e

            # Clean up partial files before retry
            for partial in [filepath, filepath + '.part', filepath + '.ytdl',
                            filepath + '.temp', filepath + '.f*.mp4', filepath + '.f*.webm']:
                if os.path.exists(partial):
                    try:
                        os.remove(partial)
                    except OSError:
                        pass

            base_backoff = min(2 * (i + 1), 15)
            jitter = random.uniform(0, 2)
            backoff = base_backoff + jitter
            logger.warning("YT download attempt %d failed: %s — backing off %.1fs...",
                           i + 1, error_str[:120], backoff)

            if i < max_attempts - 1:
                time.sleep(backoff)
            continue

    logger.error("❌ ALL %d download strategies exhausted", max_attempts)
    raise last_error


def download_via_direct_url(info_dict, filepath, res_height):
    """Download using direct stream URLs from Invidious/Piped API fallback.
    Used when yt-dlp extraction works via API but yt-dlp download can't."""
    formats = info_dict.get('formats', [])
    if not formats:
        return False

    # Sort by height descending, pick best match
    target = int(res_height)
    suitable = [f for f in formats if f.get('height', 0) <= target and f.get('url')]
    if not suitable:
        suitable = [f for f in formats if f.get('url')]

    if not suitable:
        return False

    # Pick highest quality within target
    suitable.sort(key=lambda x: x.get('height', 0), reverse=True)
    best = suitable[0]

    try:
        logger.info("⬇️  Direct URL download: %sp stream from API fallback", best.get('height', '?'))
        resp = http_requests.get(best['url'], stream=True, timeout=120, headers={
            "User-Agent": USER_AGENTS[0],
        })
        resp.raise_for_status()

        with open(filepath, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        if os.path.exists(filepath) and os.path.getsize(filepath) > 10000:
            logger.info("✅ Direct URL download succeeded: %s", filepath)
            return True
        else:
            logger.warning("Direct URL download produced tiny/empty file")
            if os.path.exists(filepath):
                os.remove(filepath)
            return False

    except Exception as e:
        logger.error("Direct URL download failed: %s", str(e)[:120])
        if os.path.exists(filepath):
            os.remove(filepath)
        return False


# ── Error Classification ──────────────────────────────────────
def classify_yt_error(error_msg):
    error_lower = error_msg.lower()

    # Bot detection / rate limiting
    if any(p in error_lower for p in ['sign in', 'bot', 'confirm', '429', 'too many requests',
                                       'rate limit', 'captcha', 'please sign in',
                                       'proof of origin', 'po token']):
        return "YouTube is temporarily blocking downloads from this server. Please try again in a few minutes."

    # Private / unavailable
    if any(p in error_lower for p in ['private video', 'video unavailable', 'is not available',
                                       'no longer available', 'been removed']):
        return "This video is private, deleted, or unavailable."

    # Age restriction
    if any(p in error_lower for p in ['age', 'login_required', 'sign_in_required']):
        return "This video is age-restricted and requires authentication."

    # Geo restriction
    if any(p in error_lower for p in ['geo', 'not available in your country', 'blocked in your']):
        return "This video is not available in the server's region."

    # Copyright
    if any(p in error_lower for p in ['copyright', 'dmca', 'takedown']):
        return "This video has been removed due to copyright."

    # Live streams
    if 'live' in error_lower and ('not supported' in error_lower or 'cannot download' in error_lower):
        return "Live streams cannot be downloaded."

    # Network errors
    if any(p in error_lower for p in ['timeout', 'connection', 'network', 'ssl', 'tls']):
        return "A network error occurred. Please try again."

    # Signature / nsig / decryption errors (common when yt-dlp is outdated)
    if any(p in error_lower for p in ['nsig', 'signature', 'n_sig', 'cipher', 'decrypt']):
        return "YouTube extraction engine needs an update. Please try again later."

    # HTTP 403 Forbidden
    if '403' in error_lower or 'forbidden' in error_lower:
        return "YouTube denied access. Please try again in a few minutes."

    # Extraction / format errors
    if any(p in error_lower for p in ['no video formats', 'cannot parse', 'unable to extract',
                                       'unsupported url']):
        return "Could not extract video data. The URL may be invalid or the video format is unsupported."

    return "Could not process this video. Please check the URL and try again."


# ── File Cleanup ──────────────────────────────────────────────
def delete_file_delayed(filepath, delay=1800):
    def task():
        time.sleep(delay)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info("Auto-deleted: %s", filepath)
        except Exception as e:
            logger.error("Error deleting file %s: %s", filepath, e)
    threading.Thread(target=task, daemon=True).start()


def cleanup_old_files():
    while True:
        now = time.time()
        if os.path.exists(DOWNLOAD_DIR):
            for f in os.listdir(DOWNLOAD_DIR):
                file_path = os.path.join(DOWNLOAD_DIR, f)
                try:
                    if os.path.isfile(file_path) and os.stat(file_path).st_mtime < now - FILE_EXPIRY_TIME:
                        os.remove(file_path)
                        logger.info("Deleted old file: %s", f)
                except Exception as e:
                    logger.error("Error deleting file %s: %s", f, e)
        time.sleep(300)


cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()


# ── Routes ────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/get_info', methods=['POST'])
@limiter.limit("30/minute")
def get_info():
    data = request.get_json(silent=True) or {}
    video_url = data.get('url', '').strip()

    if not video_url:
        return jsonify({"error": "No URL provided!"}), 400

    yt_regex = r'(https?://(?:www\.|m\.|music\.)?(?:youtube\.com|youtu\.be)/.+)'
    if not re.match(yt_regex, video_url):
        return jsonify({"error": "Sorry, this downloader only supports YouTube videos and Shorts."}), 400

    # ── Redis Cache Check ─────────────────────────────────────
    cached = cache_get('yt_info', video_url)
    if cached:
        logger.info("🎯 Cache HIT for: %s", video_url[:60])
        return jsonify(cached)

    try:
        info_dict, strategy_idx = extract_with_retry(video_url)

        raw_title = info_dict.get('title')
        description = info_dict.get('description')

        title = ""
        if raw_title and not raw_title.startswith("Video by "):
            title = raw_title
        elif description and len(description.strip()) > 0:
            title = " ".join(description.splitlines())[:60] + "..."
        else:
            title = "YouTube_Video"

        thumbnail = ""
        if info_dict.get('thumbnail'):
            thumbnail = info_dict['thumbnail']
        elif info_dict.get('thumbnails'):
            for tb in reversed(info_dict['thumbnails']):
                if tb.get('url'):
                    thumbnail = tb['url']
                    break

        if thumbnail:
            thumbnail = f"/api/thumb_proxy?url={quote(thumbnail, safe='')}"

        available_formats = [
            {"resolution": "1080p (Full HD)", "height": 1080},
            {"resolution": "720p (HD)", "height": 720},
            {"resolution": "480p (SD)", "height": 480},
            {"resolution": "360p", "height": 360},
        ]

        result = {
            "title": title,
            "thumbnail": thumbnail,
            "formats": available_formats
        }

        # ── Cache result for 10 minutes ───────────────────────
        cache_set('yt_info', video_url, result, ttl=600)

        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = str(e)
        user_message = classify_yt_error(error_msg)
        return jsonify({"error": user_message}), 500


# ── SSRF-Safe Thumbnail Proxy ─────────────────────────────────
THUMB_ALLOWED_DOMAINS = [
    'i.ytimg.com', 'img.youtube.com', 'yt3.ggpht.com',
    'i.imgur.com', 'lh3.googleusercontent.com',
    'cdninstagram.com', 'scontent.cdninstagram.com',
    'p16-sign-sg.tiktokcdn.com', 'p16-sign-va.tiktokcdn.com',
    'scontent.xx.fbcdn.net', 'external.xx.fbcdn.net',
]
MAX_THUMB_SIZE = 5 * 1024 * 1024  # 5MB max thumbnail

def _is_thumb_url_safe(url):
    """Validate thumbnail URL against allowlist to prevent SSRF."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False
        host = parsed.hostname or ''
        # Allow any subdomain of allowed domains
        return any(host == d or host.endswith('.' + d) for d in THUMB_ALLOWED_DOMAINS)
    except Exception:
        return False

@app.route('/api/thumb_proxy')
@limiter.limit("60/minute")
def thumb_proxy():
    img_url = request.args.get('url', '')
    if not img_url:
        return jsonify({"error": "No URL"}), 400

    if not _is_thumb_url_safe(img_url):
        return jsonify({"error": "URL not allowed"}), 403

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.youtube.com/"
        }
        resp = http_requests.get(img_url, headers=headers, timeout=10, stream=True)
        if resp.status_code != 200:
            return jsonify({"error": "Thumbnail not available"}), 404

        # Stream with size limit to prevent memory exhaustion
        def generate():
            downloaded = 0
            for chunk in resp.iter_content(chunk_size=8192):
                downloaded += len(chunk)
                if downloaded > MAX_THUMB_SIZE:
                    break
                yield chunk

        return Response(
            generate(),
            content_type=resp.headers.get('Content-Type', 'image/jpeg'),
            headers={'Cache-Control': 'public, max-age=3600'}
        )
    except Exception:
        return jsonify({"error": "Thumbnail fetch failed"}), 500


@app.route('/api/download')
@limiter.limit("10/minute")
def download_video():
    video_url = request.args.get('url')
    res_height = request.args.get('res', '720')
    req_title = request.args.get('title', 'YouTube_Video')

    if not video_url:
        return jsonify({"error": "URL Missing"}), 400

    safe_title = re.sub(r'[\\/*?:"<>|]', "", req_title).strip()
    if not safe_title:
        safe_title = "YouTube_Video"

    unique_filename = f"YT_Video_{uuid.uuid4().hex[:8]}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, unique_filename)
    user_download_name = f"{safe_title}.mp4"

    try:
        logger.info("⬇️  Downloading: %s at %sp", video_url, res_height)

        # First try standard yt-dlp download with retry
        try:
            download_with_retry(video_url, filepath, res_height)
        except Exception as dl_err:
            # If yt-dlp download fails, try API fallback for direct URL download
            logger.warning("yt-dlp download failed, trying API fallback: %s", str(dl_err)[:100])
            api_info = extract_via_invidious_api(video_url)
            if api_info and download_via_direct_url(api_info, filepath, res_height):
                logger.info("✅ Downloaded via API fallback direct URL")
            else:
                raise dl_err  # Re-raise original error

        delete_file_delayed(filepath, delay=1800)
        logger.info("✅ Download complete: %s", unique_filename)

        # Chunked streaming — avoids loading entire video into RAM
        def stream_file():
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(64 * 1024)  # 64KB chunks
                    if not chunk:
                        break
                    yield chunk

        file_size = os.path.getsize(filepath)
        response = Response(
            stream_file(),
            mimetype='video/mp4',
            headers={
                'Content-Disposition': f'attachment; filename="{user_download_name}"',
                'Content-Length': str(file_size),
                'X-Download-Status': 'completed'
            }
        )
        response.set_cookie('download_status', 'completed', path='/')
        return response

    except Exception as e:
        import traceback
        traceback.print_exc()
        if os.path.exists(filepath):
            os.remove(filepath)
        error_msg = str(e)
        user_message = classify_yt_error(error_msg)
        return jsonify({"error": user_message}), 500

# ── Async Download Routes (Celery-powered) ───────────────────
@app.route('/api/download_async', methods=['POST'])
@limiter.limit("10/minute")
def download_async():
    """Submit a download task to Celery. Returns task_id for polling."""
    data = request.get_json(silent=True) or {}
    video_url = data.get('url', '').strip()
    res_height = data.get('res', '720')
    req_title = data.get('title', 'YouTube_Video')

    if not video_url:
        return jsonify({"error": "URL Missing"}), 400

    yt_regex = r'(https?://(?:www\.|m\.|music\.)?(?:youtube\.com|youtu\.be)/.+)'
    if not re.match(yt_regex, video_url):
        return jsonify({"error": "Invalid YouTube URL"}), 400

    try:
        from tasks import celery_download_yt
        task = celery_download_yt.delay(video_url, res_height, req_title)
        logger.info("📋 Queued download task: %s for %s", task.id, video_url[:60])
        return jsonify({"task_id": task.id, "status": "queued"})
    except Exception as e:
        logger.error("Failed to queue task: %s", str(e)[:120])
        # Fallback: if Celery is unavailable, tell user to use sync route
        return jsonify({"error": "Task queue unavailable. Please try again."}), 503


@app.route('/api/task_status/<task_id>')
@limiter.limit("120/minute")
def task_status(task_id):
    """Poll for task progress. Frontend calls this every 1-2 seconds."""
    progress = get_progress(task_id)
    return jsonify(progress)


@app.route('/api/download_file/<task_id>')
@limiter.limit("10/minute")
def download_file(task_id):
    """Serve the completed download file via chunked streaming.
    Only works after task status is 'ready'."""
    progress = get_progress(task_id)

    if progress.get('stage') != 'ready':
        return jsonify({"error": "File not ready yet", "stage": progress.get('stage')}), 404

    filepath = progress.get('filepath')
    download_name = progress.get('download_name', 'video.mp4')

    if not filepath or not os.path.exists(filepath):
        return jsonify({"error": "File has expired or was not found"}), 410

    # Chunked streaming — avoids loading entire video into RAM
    def stream_file():
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(64 * 1024)  # 64KB chunks
                if not chunk:
                    break
                yield chunk

    file_size = os.path.getsize(filepath)
    response = Response(
        stream_file(),
        mimetype='video/mp4',
        headers={
            'Content-Disposition': f'attachment; filename="{download_name}"',
            'Content-Length': str(file_size),
            'X-Download-Status': 'completed'
        }
    )
    return response


@app.route('/sitemap.xml')
def sitemap():
    return send_file('sitemap.xml')

if __name__ == '__main__':
    app.run(debug=True, threaded=True)