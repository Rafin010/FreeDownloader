import os
import uuid
import threading
import time
import re
import logging
from urllib.parse import urlparse, quote
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
# We use rotating User-Agents and headers instead of 'impersonate'
# since curl_cffi is not installed on the server.
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
]


def build_opts(strategy_idx=0, referer_url=""):
    """Build yt-dlp options rotating User-Agents. No 'impersonate' to avoid curl_cffi dependency."""
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
        # NO 'impersonate' key — avoids curl_cffi error
    }

    if os.path.exists(COOKIES_FILE):
        opts['cookiefile'] = COOKIES_FILE

    return opts


def extract_with_retry(video_url):
    """Try extraction with rotating User-Agents."""
    last_error = None
    for i in range(len(USER_AGENTS)):
        try:
            opts = build_opts(i, video_url)
            logger.info("P_D attempt %d for: %s", i, video_url)
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                logger.info("✅ P_D attempt %d succeeded!", i)
                return info, i
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            if 'is not a valid url' in error_str:
                raise e
            logger.warning("P_D attempt %d failed: %s", i, str(e)[:100])
            continue
    raise last_error


def download_with_retry(video_url, filepath, format_string):
    """Download with rotating strategies."""
    last_error = None
    for i in range(len(USER_AGENTS)):
        try:
            opts = build_opts(i, video_url)
            opts['socket_timeout'] = 120  # Longer timeout for downloads
            opts.update({
                'format': format_string,
                'merge_output_format': 'mp4',
                'outtmpl': filepath,
            })
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([video_url])
            if os.path.exists(filepath):
                return True
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            if 'is not a valid url' in error_str:
                raise e
            for partial in [filepath, filepath + '.part', filepath + '.ytdl']:
                if os.path.exists(partial):
                    os.remove(partial)
            logger.warning("P_D download attempt %d failed: %s", i, str(e)[:120])
            continue
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
def get_info():
    data = request.json
    video_url = data.get('url')

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


@app.route('/api/thumb_proxy')
def thumb_proxy():
    img_url = request.args.get('url', '')
    referer_url = request.args.get('referer', 'https://google.com/')
    if not img_url:
        return "No URL", 400
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": referer_url
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
    req_title = request.args.get('title', 'Video')

    if not video_url:
        return "URL Missing", 400

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

        download_with_retry(video_url, filepath, format_string)

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
        user_message = classify_download_error(error_msg, platform)
        return jsonify({"error": user_message}), 500


if __name__ == '__main__':
    app.run(debug=True, threaded=True)