import os
import uuid
import threading
import time
import re
import logging
from flask import Flask, render_template, request, jsonify, send_file, make_response, Response
import yt_dlp
import requests as http_requests

app = Flask(__name__)

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


# Run diagnostics at startup
_yt_dlp_version = get_yt_dlp_version()
_has_auth_cookies = validate_yt_cookies()


# ── YouTube-specific: Multiple extraction strategies ──────────
# Updated 2026: Deprecated clients removed. Current effective set:
#   - web: Standard browser client
#   - web_embedded: Embedded player (bypasses some restrictions)
#   - mweb: Mobile web (often less restricted)
#   - android_vr: VR client (minimal bot detection)
#   - default: Let yt-dlp auto-select
STRATEGIES = [
    # Strategy 0: web_embedded — embedded player, often bypasses bot checks
    {'youtube': {'player_client': ['web_embedded']}},
    # Strategy 1: mweb — mobile web client, lighter bot detection
    {'youtube': {'player_client': ['mweb']}},
    # Strategy 2: web — standard browser client
    {'youtube': {'player_client': ['web']}},
    # Strategy 3: android_vr — VR client, minimal detection
    {'youtube': {'player_client': ['android_vr']}},
    # Strategy 4: default — let yt-dlp auto-select the best client
    {},
]

# User-Agent rotation pool
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
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
    }

    if ext_args:
        opts['extractor_args'] = ext_args

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
    ]
    error_lower = error_str.lower()
    return any(pattern in error_lower for pattern in unrecoverable)


def extract_with_retry(video_url):
    """Try ALL strategies with exponential backoff. Cycles through strategies twice (10 attempts)."""
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

            # Exponential backoff: 2s, 4s, 6s, 8s, 10s, ... capped at 15s
            backoff = min(2 * (i + 1), 15)
            logger.warning("YT attempt %d failed: %s — backing off %ds before next...",
                           i + 1, error_str[:120], backoff)

            if i < max_attempts - 1:
                time.sleep(backoff)
            continue

    # All attempts exhausted — log detailed diagnostic info
    logger.error("❌ ALL %d YouTube strategies exhausted for: %s", max_attempts, video_url)
    logger.error("   Last error: %s", str(last_error))
    logger.error("   yt-dlp version: %s | curl-cffi: %s | auth cookies: %s",
                 _yt_dlp_version, _HAS_CURL_CFFI, _has_auth_cookies)
    raise last_error


def download_with_retry(video_url, filepath, res_height):
    """Download video using multiple strategies with exponential backoff."""
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

            backoff = min(2 * (i + 1), 15)
            logger.warning("YT download attempt %d failed: %s — backing off %ds...",
                           i + 1, error_str[:120], backoff)

            if i < max_attempts - 1:
                time.sleep(backoff)
            continue

    logger.error("❌ ALL %d download strategies exhausted", max_attempts)
    raise last_error


# ── Error Classification ──────────────────────────────────────
def classify_yt_error(error_msg):
    error_lower = error_msg.lower()

    # Bot detection / rate limiting
    if any(p in error_lower for p in ['sign in', 'bot', 'confirm', '429', 'too many requests',
                                       'rate limit', 'captcha']):
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
def get_info():
    data = request.json
    video_url = data.get('url')

    if not video_url:
        return jsonify({"error": "No URL provided!"}), 400

    yt_regex = r'(https?://(?:www\.)?(?:youtube\.com|youtu\.be|youtube\.com/shorts)/.+)'
    if not re.match(yt_regex, video_url):
        return jsonify({"error": "Sorry, this downloader only supports YouTube videos and Shorts."}), 400

    try:
        info_dict, _ = extract_with_retry(video_url)

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
            from urllib.parse import quote
            thumbnail = f"/api/thumb_proxy?url={quote(thumbnail, safe='')}"

        available_formats = [
            {"resolution": "1080p (Full HD)", "height": 1080},
            {"resolution": "720p (HD)", "height": 720},
            {"resolution": "480p (SD)", "height": 480},
            {"resolution": "360p", "height": 360},
        ]

        return jsonify({
            "title": title,
            "thumbnail": thumbnail,
            "formats": available_formats
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = str(e)
        user_message = classify_yt_error(error_msg)
        return jsonify({"error": user_message}), 500


@app.route('/api/thumb_proxy')
def thumb_proxy():
    img_url = request.args.get('url', '')
    if not img_url:
        return "No URL", 400
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.youtube.com/"
        }
        resp = http_requests.get(img_url, headers=headers, timeout=10, stream=True)
        if resp.status_code == 200:
            return Response(
                resp.content,
                content_type=resp.headers.get('Content-Type', 'image/jpeg'),
                headers={'Cache-Control': 'public, max-age=3600'}
            )
        return "Thumbnail not available", 404
    except Exception:
        return "Thumbnail fetch failed", 500


@app.route('/api/download')
def download_video():
    video_url = request.args.get('url')
    res_height = request.args.get('res', '720')
    req_title = request.args.get('title', 'YouTube_Video')

    if not video_url:
        return "URL Missing", 400

    safe_title = re.sub(r'[\\/*?:"<>|]', "", req_title).strip()
    if not safe_title:
        safe_title = "YouTube_Video"

    unique_filename = f"YT_Video_{uuid.uuid4().hex[:8]}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, unique_filename)
    user_download_name = f"{safe_title}.mp4"

    try:
        logger.info("⬇️  Downloading: %s at %sp", video_url, res_height)

        download_with_retry(video_url, filepath, res_height)

        delete_file_delayed(filepath, delay=1800)
        logger.info("✅ Download complete: %s", unique_filename)

        response = make_response(send_file(
            filepath,
            as_attachment=True,
            download_name=user_download_name,
            mimetype='video/mp4'
        ))
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


if __name__ == '__main__':
    app.run(debug=True, threaded=True)