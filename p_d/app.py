import os
import sys
import uuid
import threading
import time
import re
import random
import logging
from urllib.parse import urlparse, quote
from flask import Flask, render_template, request, jsonify, send_file, Response
import yt_dlp
import requests as http_requests
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infra.redis_client import get_limiter_storage_uri, cache_get, cache_set
from infra.progress import get_progress
from infra.api_extractors import extract_video, download_video_stream

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
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

FILE_EXPIRY_TIME = 1800  # 30 minutes

# ── Check if curl-cffi is available for browser impersonation ──
_HAS_CURL_CFFI = False
try:
    import curl_cffi  # noqa: F401
    logger.warning("⚠️  curl-cffi installed but impersonation targets not available. Skipping.")
except ImportError:
    logger.warning("⚠️  curl-cffi not installed — browser impersonation DISABLED.")


# ── Utility: Get Platform Name ─────────────────────────────────
def get_platform_name(url):
    """Extracts domain name from URL for dynamic logging and user messages."""
    try:
        domain = urlparse(url).netloc
        domain = domain.replace('www.', '').split('.')[0].capitalize()
        return domain if domain else "Website"
    except:
        return "Website"


# ── Multi-Strategy Options Builder ────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/19.2 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
]


def build_opts(strategy_idx=0, referer_url=""):
    """Build yt-dlp options rotating User-Agents with full hardening."""
    ua = USER_AGENTS[strategy_idx % len(USER_AGENTS)]
    headers = {
        "User-Agent": ua,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    if referer_url:
        headers["Referer"] = referer_url

    opts = {
        'quiet': True,
        'no_warnings': True,
        'http_headers': headers,
        'socket_timeout': 30,
        'force_ipv4': True,
        # SSL: prefer verified certs, fallback handled in retry logic
        'nocheckcertificate': False,
        # Rate limiting: sleep between requests
        'sleep_interval': 1,
        'max_sleep_interval': 4,
        'sleep_interval_requests': 1,
        # Retry internal downloads
        'retries': 5,
        'fragment_retries': 5,
    }

    if os.path.exists(COOKIES_FILE):
        opts['cookiefile'] = COOKIES_FILE

    return opts


def extract_with_retry(video_url):
    """Try API extraction first (SnagSave-style), then yt-dlp with rotating UAs."""
    last_error = None
    num_attempts = len(USER_AGENTS)
    platform = get_platform_name(video_url)

    # ── Pass 0 (NEW): Multi-API Extraction ── SnagSave-style ──
    logger.info("🚀 Pass 0: Trying API extraction (Cobalt) for %s: %s", platform, video_url[:60])
    try:
        # Cobalt works well for many adult sites too
        api_result = extract_video(video_url, platform='auto', quality='1080')
        if api_result and api_result.get('download_url'):
            logger.info("✅ API extraction succeeded via %s", api_result.get('source', 'api'))
            info = {
                'title': api_result.get('title', f'{platform}_Video'),
                'description': api_result.get('title', ''),
                'thumbnail': api_result.get('thumbnail', ''),
                'thumbnails': [{'url': api_result.get('thumbnail', '')}] if api_result.get('thumbnail') else [],
                'formats': [],
                '_api_download_url': api_result.get('download_url'),
                '_api_source': api_result.get('source', 'api'),
            }
            return info, -1
    except Exception as api_err:
        logger.warning("API extraction failed: %s — falling back to yt-dlp", str(api_err)[:100])

    # ── Pass 1: yt-dlp with rotating User-Agents ──
    for i in range(num_attempts):
        try:
            opts = build_opts(i, video_url)
            logger.info("P_D attempt %d/%d for: %s", i + 1, num_attempts, video_url)
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                logger.info("✅ P_D attempt %d succeeded!", i + 1)
                return info, i
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            if 'is not a valid url' in error_str:
                raise e

            backoff = min(2 * (i + 1), 8) + random.uniform(0, 1)
            logger.warning("P_D attempt %d failed: %s — backing off %.1fs...",
                           i + 1, str(e)[:120], backoff)

            if i < num_attempts - 1:
                time.sleep(backoff)
            continue

    logger.error("❌ ALL P_D strategies exhausted for: %s", video_url)
    raise last_error


def download_with_retry(video_url, filepath, format_string):
    """Download with rotating strategies, jittered backoff, and retry on transient errors."""
    last_error = None
    num_attempts = len(USER_AGENTS)

    for i in range(num_attempts):
        try:
            opts = build_opts(i, video_url)
            opts['socket_timeout'] = 120  # Longer timeout for downloads
            opts.update({
                'format': format_string,
                'merge_output_format': 'mp4',
                'outtmpl': filepath,
            })
            logger.info("P_D download attempt %d/%d", i + 1, num_attempts)
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([video_url])
            if os.path.exists(filepath):
                logger.info("✅ P_D download attempt %d succeeded!", i + 1)
                return True
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            if 'is not a valid url' in error_str:
                raise e
            for partial in [filepath, filepath + '.part', filepath + '.ytdl']:
                if os.path.exists(partial):
                    try:
                        os.remove(partial)
                    except OSError:
                        pass

            base_backoff = min(2 * (i + 1), 10)
            jitter = random.uniform(0, 1.5)
            backoff = base_backoff + jitter
            logger.warning("P_D download attempt %d failed: %s — backing off %.1fs...",
                           i + 1, str(e)[:120], backoff)

            if i < num_attempts - 1:
                time.sleep(backoff)
            continue

    logger.error("❌ ALL P_D download strategies exhausted")
    raise last_error


# ── Error Classification ──────────────────────────────────────
def classify_download_error(error_msg, platform="Website"):
    error_lower = error_msg.lower()
    if 'sign in' in error_lower or 'bot' in error_lower or 'login' in error_lower:
        return f"{platform} is restricting access. Please try again later."
    if 'private' in error_lower or 'unavailable' in error_lower or 'not available' in error_lower:
        return f"This {platform} video is private, deleted, or region-restricted."
    if 'unsupported' in error_lower or 'no video' in error_lower:
        return f"This URL doesn't contain a downloadable video or the platform is not supported."
    if 'impersonate' in error_lower:
        return f"Server configuration issue. Please contact admin."
    return f"Could not process this video from {platform}. It might be protected or invalid."


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

    if not video_url.startswith("http"):
        return jsonify({"error": "Invalid URL format."}), 400

    platform = get_platform_name(video_url)

    try:
        info_dict, _ = extract_with_retry(video_url)

        raw_title = info_dict.get('title')
        description = info_dict.get('description')

        title = ""
        if raw_title:
            title = raw_title
        elif description and len(description.strip()) > 0:
            title = " ".join(description.splitlines())[:60] + "..."
        else:
            title = f"{platform}_Video"

        thumbnail = ""
        if info_dict.get('thumbnail'):
            thumbnail = info_dict['thumbnail']
        elif info_dict.get('thumbnails'):
            for tb in reversed(info_dict['thumbnails']):
                if tb.get('url'):
                    thumbnail = tb['url']
                    break

        if thumbnail:
            thumbnail = f"/api/thumb_proxy?url={quote(thumbnail, safe='')}&referer={quote(video_url, safe='')}"

        # Dynamically fetch available formats
        available_formats = []
        formats_processed = set()

        if 'formats' in info_dict:
            for f in info_dict['formats']:
                h = f.get('height')
                if h and h >= 360 and f.get('vcodec') != 'none':
                    if h not in formats_processed:
                        formats_processed.add(h)
                        res_name = f"{h}p"
                        if h == 2160: res_name += " (4K)"
                        elif h == 1440: res_name += " (2K)"
                        elif h == 1080: res_name += " (Full HD)"
                        elif h == 720: res_name += " (HD)"
                        available_formats.append({"resolution": res_name, "height": h})

            available_formats = sorted(available_formats, key=lambda k: k['height'], reverse=True)

        if not available_formats:
            available_formats = [{"resolution": "Best Available Quality", "height": "best"}]

        logger.info("✅ Info fetched for: %s (%s)", video_url, platform)

        return jsonify({
            "title": title,
            "thumbnail": thumbnail,
            "formats": available_formats
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = str(e)
        user_message = classify_download_error(error_msg, platform)
        return jsonify({"error": user_message}), 500


# ── SSRF-Safe Thumbnail Proxy ─────────────────────────────────
MAX_THUMB_SIZE = 5 * 1024 * 1024  # 5MB max

def _is_thumb_url_safe(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False
        # For the generic downloader, block internal/private IPs only
        host = parsed.hostname or ''
        if host in ('localhost', '127.0.0.1', '0.0.0.0') or host.startswith('169.254.') or host.startswith('10.') or host.startswith('192.168.'):
            return False
        return True
    except Exception:
        return False

@app.route('/api/thumb_proxy')
@limiter.limit("60/minute")
def thumb_proxy():
    img_url = request.args.get('url', '')
    referer_url = request.args.get('referer', 'https://google.com/')
    if not img_url:
        return jsonify({"error": "No URL"}), 400
    if not _is_thumb_url_safe(img_url):
        return jsonify({"error": "URL not allowed"}), 403
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": referer_url
        }
        resp = http_requests.get(img_url, headers=headers, timeout=10, stream=True)
        if resp.status_code != 200:
            return jsonify({"error": "Thumbnail not available"}), 404
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
    res_height = request.args.get('res', '1080')
    req_title = request.args.get('title', 'Video')

    if not video_url:
        return jsonify({"error": "URL Missing"}), 400

    platform = get_platform_name(video_url)

    safe_title = re.sub(r'[\\/*?:"<>|]', "", req_title).strip()
    if not safe_title:
        safe_title = f"{platform}_Video"

    unique_filename = f"{platform}_{uuid.uuid4().hex[:8]}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, unique_filename)
    user_download_name = f"{safe_title}.mp4"

    if res_height == 'best':
        format_string = 'bestvideo+bestaudio/best'
    else:
        format_string = f'bestvideo[height<={res_height}]+bestaudio/best[height<={res_height}]/best'

    try:
        logger.info("⬇️  Downloading %s: %s at %s", platform, video_url, res_height)

        download_success = False

        # ── NEW: Try API-based download first (SnagSave-style) ──
        try:
            api_result = extract_video(video_url, platform='auto', quality=res_height)
            if api_result and api_result.get('download_url'):
                logger.info("⬇️  P_D downloading via API: %s", api_result.get('source', 'api'))
                download_success = download_video_stream(
                    api_result['download_url'], filepath
                )
                if download_success:
                    logger.info("✅ P_D API download succeeded!")
        except Exception as api_err:
            logger.warning("P_D API download failed: %s — falling back to yt-dlp", str(api_err)[:100])

        # ── Fallback: yt-dlp download ──
        if not download_success:
            download_with_retry(video_url, filepath, format_string)

        delete_file_delayed(filepath, delay=1800)
        logger.info("✅ Download complete: %s", unique_filename)

        def stream_file():
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(64 * 1024)
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
        user_message = classify_download_error(error_msg, platform)
        return jsonify({"error": user_message}), 500

# ── Async Download Routes (Celery-powered) ───────────────────
@app.route('/api/download_async', methods=['POST'])
@limiter.limit("10/minute")
def download_async():
    data = request.get_json(silent=True) or {}
    video_url = data.get('url', '').strip()
    res_height = data.get('res', '720')
    req_title = data.get('title', 'Video')
    if not video_url:
        return jsonify({"error": "URL Missing"}), 400
    try:
        from tasks import celery_download_pd
        task = celery_download_pd.delay(video_url, res_height, req_title)
        return jsonify({"task_id": task.id, "status": "queued"})
    except Exception as e:
        return jsonify({"error": "Task queue unavailable. Please try again."}), 503

@app.route('/api/task_status/<task_id>')
@limiter.limit("120/minute")
def task_status(task_id):
    return jsonify(get_progress(task_id))

@app.route('/api/download_file/<task_id>')
@limiter.limit("10/minute")
def download_file(task_id):
    progress = get_progress(task_id)
    if progress.get('stage') != 'ready':
        return jsonify({"error": "File not ready yet"}), 404
    filepath = progress.get('filepath')
    download_name = progress.get('download_name', 'video.mp4')
    if not filepath or not os.path.exists(filepath):
        return jsonify({"error": "File has expired or was not found"}), 410
    def stream_file():
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(64 * 1024)
                if not chunk: break
                yield chunk
    file_size = os.path.getsize(filepath)
    return Response(stream_file(), mimetype='video/mp4', headers={
        'Content-Disposition': f'attachment; filename="{download_name}"',
        'Content-Length': str(file_size),
    })

@app.route('/sitemap.xml')
def sitemap():
    return send_file('sitemap.xml')


@app.route('/sitemap.xml')
def serve_sitemap():
    import os
    from flask import send_from_directory
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'sitemap.xml')

@app.route('/robots.txt')
def serve_robots():
    import os
    from flask import send_from_directory
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'robots.txt')

if __name__ == '__main__':
    app.run(debug=True, threaded=True)