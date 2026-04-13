import os
import uuid
import threading
import time
import re
import random
import logging
from flask import Flask, render_template, request, jsonify, send_file, Response
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


# ── Cookie validation on startup ──────────────────────────────
def validate_fb_cookies():
    """Check if cookies.txt contains real Facebook session cookies."""
    if not os.path.exists(COOKIES_FILE):
        logger.warning("⚠️  No cookies.txt found at %s — Facebook may block unauthenticated requests.", COOKIES_FILE)
        return False

    try:
        with open(COOKIES_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().strip()

        if not content or content.startswith('# Netscape') and len(content) < 100:
            logger.warning("⚠️  cookies.txt is empty or contains no session data. "
                           "Export cookies from a logged-in Facebook browser session for reliable downloads.")
            return False

        # Check for Facebook authenticated session markers
        auth_markers = ['c_user', 'xs', 'datr', 'sb', 'fr']
        found = [m for m in auth_markers if m in content]

        if found:
            logger.info("✅ cookies.txt contains Facebook session cookies: %s", ', '.join(found))
            return True
        else:
            logger.warning("⚠️  cookies.txt exists but has no Facebook session cookies. "
                           "Export from a logged-in session for reliable downloads.")
            return False
    except Exception as e:
        logger.warning("⚠️  Could not read cookies.txt: %s", e)
        return False


_has_fb_cookies = validate_fb_cookies()


# ── URL Normalization & Validation ────────────────────────────
# Expanded regex: matches facebook.com (with or without any subdomain),
# fb.watch, fb.gg, fb.com, l.facebook.com, lm.facebook.com,
# plus explicit reel, stories, and watch paths.
FB_URL_REGEX = re.compile(
    r'https?://'
    r'(?:[\w-]+\.)*'                          # any subdomain (www, m, web, l, lm, etc.)
    r'(?:facebook\.com|fb\.watch|fb\.gg|fb\.com)'  # core domains
    r'(?:/\S*)?',                              # path (optional)
    re.IGNORECASE
)


def normalize_fb_url(url):
    """Resolve redirects and normalize Facebook URLs for reliable extraction.
    - Resolves fb.watch, l.facebook.com redirects
    - Adds www. prefix if missing
    - Converts m.facebook.com to www.facebook.com
    - Normalizes reel/watch URLs
    Returns the normalized URL, or the original URL if resolution fails."""
    try:
        # Follow redirects with a real browser User-Agent
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        # Step 1: Resolve shortlink/redirect domains
        needs_resolution = any(domain in url.lower() for domain in
                                ['fb.watch', 'l.facebook.com', 'lm.facebook.com',
                                 '/share/r/', '/share/v/', '/share/p/'])

        if needs_resolution:
            logger.info("🔗 Resolving redirect URL: %s", url)
            try:
                resp = http_requests.head(url, headers=headers, allow_redirects=True, timeout=10)
                resolved = resp.url
                if resolved and resolved != url:
                    logger.info("🔗 Resolved to: %s", resolved)
                    url = resolved
            except Exception as e:
                logger.warning("Redirect resolution failed: %s — continuing with original URL", str(e)[:80])

        # Step 2: Normalize m.facebook.com → www.facebook.com
        url = re.sub(r'https?://m\.facebook\.com', 'https://www.facebook.com', url)

        # Step 3: Add www. prefix if missing (facebook.com → www.facebook.com)
        url = re.sub(r'https?://facebook\.com', 'https://www.facebook.com', url)

        # Step 4: Ensure https
        if url.startswith('http://'):
            url = url.replace('http://', 'https://', 1)

        # Step 5: Clean tracking parameters but keep video identifiers
        # Remove fbclid, mibextid, etc. but keep video_id, v, id parameters
        url = re.sub(r'[?&](?:fbclid|mibextid|__cft__\[\d+\]|__tn__|refid|ref)=[^&]*', '', url)
        # Clean up leftover ? or & at end
        url = re.sub(r'[?&]$', '', url)

        return url

    except Exception as e:
        logger.warning("URL normalization failed for %s: %s — using original URL", url, str(e)[:80])
        return url


def extract_fb_video_id(url):
    """Extract a Facebook video ID from various URL formats."""
    patterns = [
        r'/videos/(\d+)',
        r'/video/(\d+)',
        r'/reel/(\d+)',
        r'/watch/?\?v=(\d+)',
        r'story_fbid=(\d+)',
        r'/posts/(\d+)',
        r'video_id=(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def build_mobile_url(url):
    """Convert a Facebook URL to its mobile equivalent for lighter extraction."""
    mobile_url = re.sub(r'https?://(?:www\.)?facebook\.com', 'https://m.facebook.com', url)
    return mobile_url


def build_embed_url(url):
    """Build a Facebook video embed URL from a video ID for fallback extraction."""
    video_id = extract_fb_video_id(url)
    if video_id:
        return f"https://www.facebook.com/video/embed/?video_id={video_id}"
    return None


def is_valid_fb_url(url):
    """Validate if a URL is a Facebook video URL."""
    return bool(FB_URL_REGEX.match(url))


# ── Multi-Strategy Extraction ─────────────────────────────────
# Facebook blocks based on User-Agent, TLS fingerprint, and cookie state.
# We rotate through multiple strategies with different configurations.

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/19.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 19_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/19.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0",
]

# Extraction strategies: different extractor configurations for Facebook
FB_STRATEGIES = [
    # Strategy 0: Default — standard extraction
    {'name': 'default', 'extractor_args': {}},
    # Strategy 1: Force Facebook extractor with mobile UA hint
    {'name': 'mobile_hint', 'extractor_args': {'facebook': {'format_sort': ['quality']}}},
    # Strategy 2: Generic extractor fallback
    {'name': 'generic', 'extractor_args': {}, 'extra': {'force_generic_extractor': True}},
]


def get_ydl_opts_for_attempt(attempt=0, strategy_idx=0):
    """Build yt-dlp options rotating User-Agent and strategy on each attempt."""
    ua = USER_AGENTS[attempt % len(USER_AGENTS)]
    strategy = FB_STRATEGIES[strategy_idx % len(FB_STRATEGIES)]

    headers = {
        "User-Agent": ua,
        "Referer": "https://www.facebook.com/",
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
        # Rate limiting: sleep between requests
        'sleep_interval': 1,
        'max_sleep_interval': 4,
        'sleep_interval_requests': 1,
        # Retry internal downloads
        'retries': 3,
        'fragment_retries': 3,
        # Don't fail on certificate issues in some VPS environments
        'nocheckcertificate': True,
    }

    # Apply strategy-specific options
    if strategy.get('extractor_args'):
        opts['extractor_args'] = strategy['extractor_args']
    if strategy.get('extra'):
        opts.update(strategy['extra'])

    # Browser TLS impersonation (requires curl-cffi)
    if _HAS_CURL_CFFI:
        opts['impersonate'] = 'chrome'

    if os.path.exists(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 10:
        opts['cookiefile'] = COOKIES_FILE

    return opts


def _is_unrecoverable_fb_error(error_str):
    """Check if a Facebook error is truly unrecoverable."""
    unrecoverable = [
        'is not a valid url',
        'private video',
        "this content isn't available",
        'removed',
        'does not exist',
    ]
    error_lower = error_str.lower()
    return any(pattern in error_lower for pattern in unrecoverable)


def extract_with_retry(video_url):
    """Multi-pass extraction with escalating fallback strategies:
    Pass 1: Original URL with all UA rotations and strategies
    Pass 2: Resolved/normalized URL (if different)
    Pass 3: Mobile site URL variant
    Pass 4: Embedded player URL (lightest auth requirements)
    Each pass rotates through User-Agents with jittered exponential backoff."""
    last_error = None
    num_ua = len(USER_AGENTS)
    num_strategies = len(FB_STRATEGIES)

    # ── Pass 1: Original URL with strategy rotation ───────────
    for s in range(num_strategies):
        for i in range(num_ua):
            try:
                strategy_name = FB_STRATEGIES[s]['name']
                logger.info("FB attempt UA=%d Strategy=%s for: %s",
                            i + 1, strategy_name, video_url[:80])
                opts = get_ydl_opts_for_attempt(i, s)

                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(video_url, download=False)
                    logger.info("✅ FB extraction succeeded! (UA=%d, Strategy=%s)", i + 1, strategy_name)
                    return info, i

            except Exception as e:
                last_error = e
                error_str = str(e)

                if _is_unrecoverable_fb_error(error_str):
                    logger.error("❌ Unrecoverable FB error: %s", error_str[:150])
                    raise e

                # Jittered exponential backoff
                base_backoff = min(2 * (i + 1), 8)
                jitter = random.uniform(0, 1.5)
                backoff = base_backoff + jitter
                logger.warning("FB attempt failed (UA=%d, %s): %s — backing off %.1fs...",
                               i + 1, strategy_name, error_str[:100], backoff)

                if not (s == num_strategies - 1 and i == num_ua - 1):
                    time.sleep(backoff)
                continue

    # ── Pass 2: Resolved/Normalized URL ───────────────────────
    resolved_url = normalize_fb_url(video_url)
    if resolved_url != video_url:
        logger.info("🔄 Pass 2: Retrying with resolved URL: %s", resolved_url[:80])
        for i in range(min(3, num_ua)):
            try:
                opts = get_ydl_opts_for_attempt(i, 0)
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(resolved_url, download=False)
                    logger.info("✅ FB resolved-URL attempt %d succeeded!", i + 1)
                    return info, i

            except Exception as e:
                last_error = e
                if _is_unrecoverable_fb_error(str(e)):
                    raise e
                backoff = min(2 * (i + 1), 8) + random.uniform(0, 1)
                logger.warning("FB resolved-URL attempt %d failed: %s — backing off %.1fs...",
                               i + 1, str(e)[:100], backoff)
                if i < 2:
                    time.sleep(backoff)
                continue

    # ── Pass 3: Mobile Site URL ───────────────────────────────
    mobile_url = build_mobile_url(resolved_url or video_url)
    logger.info("🔄 Pass 3: Trying mobile site URL: %s", mobile_url[:80])
    for i in range(min(2, num_ua)):
        try:
            opts = get_ydl_opts_for_attempt(i, 0)
            # Override UA to mobile for mobile site
            opts['http_headers']['User-Agent'] = USER_AGENTS[4]  # iPhone UA
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(mobile_url, download=False)
                logger.info("✅ FB mobile-site attempt %d succeeded!", i + 1)
                return info, i

        except Exception as e:
            last_error = e
            if _is_unrecoverable_fb_error(str(e)):
                raise e
            backoff = 3 + random.uniform(0, 2)
            logger.warning("FB mobile-site attempt %d failed: %s", i + 1, str(e)[:100])
            if i < 1:
                time.sleep(backoff)
            continue

    # ── Pass 4: Embedded Player URL ───────────────────────────
    embed_url = build_embed_url(resolved_url or video_url)
    if embed_url:
        logger.info("🔄 Pass 4: Trying embed URL: %s", embed_url)
        for i in range(min(2, num_ua)):
            try:
                opts = get_ydl_opts_for_attempt(i, 0)
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(embed_url, download=False)
                    logger.info("✅ FB embed-URL attempt %d succeeded!", i + 1)
                    return info, i

            except Exception as e:
                last_error = e
                if _is_unrecoverable_fb_error(str(e)):
                    raise e
                logger.warning("FB embed-URL attempt %d failed: %s", i + 1, str(e)[:100])
                if i < 1:
                    time.sleep(2 + random.uniform(0, 1))
                continue

    logger.error("❌ ALL Facebook extraction strategies exhausted for: %s", video_url)
    logger.error("   Last error: %s", str(last_error))
    logger.error("   curl-cffi: %s | fb cookies: %s", _HAS_CURL_CFFI, _has_fb_cookies)
    raise last_error


def download_with_retry(video_url, filepath, res_height):
    """Download video with rotating User-Agents, jittered exponential backoff,
    and retry on ALL transient errors."""
    last_error = None
    num_attempts = len(USER_AGENTS)

    for i in range(num_attempts):
        try:
            opts = get_ydl_opts_for_attempt(i, 0)
            opts['socket_timeout'] = 120  # Longer timeout for downloads
            opts.update({
                'format': f'bestvideo[height<={res_height}]+bestaudio/best[height<={res_height}]/best',
                'merge_output_format': 'mp4',
                'outtmpl': filepath,
            })

            logger.info("FB download attempt %d/%d", i + 1, num_attempts)

            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([video_url])

            if os.path.exists(filepath):
                logger.info("✅ FB download attempt %d succeeded!", i + 1)
                return True

        except Exception as e:
            last_error = e
            error_str = str(e)

            if _is_unrecoverable_fb_error(error_str):
                raise e

            # Clean up partial files before retry
            for partial in [filepath, filepath + '.part', filepath + '.ytdl',
                            filepath + '.temp']:
                if os.path.exists(partial):
                    try:
                        os.remove(partial)
                    except OSError:
                        pass

            base_backoff = min(2 * (i + 1), 10)
            jitter = random.uniform(0, 2)
            backoff = base_backoff + jitter
            logger.warning("FB download attempt %d failed: %s — backing off %.1fs...",
                           i + 1, error_str[:120], backoff)

            if i < num_attempts - 1:
                time.sleep(backoff)
            continue

    logger.error("❌ ALL Facebook download strategies exhausted")
    raise last_error


# ── Error Classification ──────────────────────────────────────
def classify_download_error(error_msg, platform="Facebook"):
    error_lower = error_msg.lower()

    # Bot detection / login required
    if any(p in error_lower for p in ['sign in', 'bot', 'login', 'log in',
                                       'authentication', 'session', 'please log in',
                                       'you must log in', 'login_required']):
        return f"{platform} is temporarily blocking downloads. Please try again in a few minutes."

    # Private / unavailable
    if any(p in error_lower for p in ['private', 'unavailable', 'not available',
                                       'no longer available', "content isn't available",
                                       'this content', 'been removed', 'deleted',
                                       'does not exist', 'page not found']):
        return f"This {platform} video is private, deleted, or unavailable."

    # Parse / extraction failures
    if any(p in error_lower for p in ['cannot parse', 'no video formats', 'unable to extract',
                                       'unsupported url', 'no suitable', 'unable to download']):
        return f"Could not extract video data from this {platform} URL. The video may be in a restricted format."

    # Network / redirect issues
    if any(p in error_lower for p in ['403', 'forbidden', 'redirect', '404', 'not found']):
        return f"Access to this {platform} video was denied. It may be restricted or the link may have expired."

    # Timeout / connection errors
    if any(p in error_lower for p in ['timeout', 'connection', 'network', 'ssl', 'tls']):
        return f"A network error occurred while accessing {platform}. Please try again."

    # Unsupported content type
    if any(p in error_lower for p in ['unsupported', 'no video', 'not a video']):
        return f"This URL doesn't contain a downloadable {platform} video."

    # CSRF / empty response (common with missing cookies)
    if any(p in error_lower for p in ['csrf', 'empty response', 'no data', 'json']):
        return f"Could not access this {platform} video. The link may require authentication."

    # Rate limiting
    if any(p in error_lower for p in ['429', 'too many', 'rate limit', 'throttle']):
        return f"{platform} is rate-limiting requests. Please try again in a few minutes."

    return f"Could not process this {platform} video. Please check the URL and try again."


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

    # Expanded URL validation — accepts all Facebook domains/subdomains
    if not is_valid_fb_url(video_url):
        return jsonify({"error": "Sorry, this downloader only supports Facebook videos."}), 400

    try:
        info_dict, _ = extract_with_retry(video_url)

        raw_title = info_dict.get('title')
        description = info_dict.get('description')

        title = ""
        if description and len(description.strip()) > 0:
            title = " ".join(description.splitlines())[:60] + "..."
        elif raw_title and not raw_title.startswith("Video by "):
            title = raw_title
        else:
            title = "Facebook_Video"

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
            {"resolution": "1440p (2K)", "height": 1440},
            {"resolution": "1080p (Full HD)", "height": 1080},
            {"resolution": "720p (HD)", "height": 720},
            {"resolution": "480p (SD)", "height": 480},
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
        user_message = classify_download_error(error_msg, "Facebook")
        return jsonify({"error": user_message}), 500


@app.route('/api/thumb_proxy')
def thumb_proxy():
    img_url = request.args.get('url', '')
    if not img_url:
        return "No URL", 400

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.facebook.com/"
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
    res_height = request.args.get('res', '1080')
    req_title = request.args.get('title', 'Facebook_Video')

    if not video_url:
        return "URL Missing", 400

    safe_title = re.sub(r'[\\/*?:"<>|]', "", req_title).strip()
    if not safe_title:
        safe_title = "Facebook_Video"

    unique_filename = f"FB_Video_{uuid.uuid4().hex[:8]}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, unique_filename)
    user_download_name = f"{safe_title}.mp4"

    try:
        logger.info("⬇️  Downloading FB: %s at %sp", video_url, res_height)

        download_with_retry(video_url, filepath, res_height)

        delete_file_delayed(filepath, delay=1800)
        logger.info("✅ Download complete: %s", unique_filename)

        return send_file(
            filepath,
            as_attachment=True,
            download_name=user_download_name,
            mimetype='video/mp4'
        )

    except Exception as e:
        import traceback
        traceback.print_exc()

        if os.path.exists(filepath):
            os.remove(filepath)

        error_msg = str(e)
        user_message = classify_download_error(error_msg, "Facebook")
        return jsonify({"error": user_message}), 500


if __name__ == '__main__':
    app.run(debug=True, threaded=True)