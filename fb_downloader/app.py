import os
import uuid
import threading
import time
import re
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

FILE_EXPIRY_TIME = 1800  # 10 minutes


# ── Cookie Validation ─────────────────────────────────────────
def validate_cookies():
    """Check if cookies.txt exists and log status on startup."""
    if not os.path.exists(COOKIES_FILE):
        logger.info(
            "ℹ️  No cookies.txt found at: %s — Facebook downloads will work without cookies for public videos.",
            COOKIES_FILE
        )
        return False
    logger.info("✅ cookies.txt found at: %s", COOKIES_FILE)
    return True

_cookies_valid = validate_cookies()


# ── Error Classification ──────────────────────────────────────
def classify_download_error(error_msg, platform="Facebook"):
    """Classify a yt-dlp error into a user-friendly message."""
    error_lower = error_msg.lower()
    
    if 'sign in' in error_lower or 'bot' in error_lower or 'login' in error_lower:
        logger.error("🚫 Auth/bot block on %s: %s", platform, error_msg)
        return (
            f"{platform} is temporarily blocking our server. "
            "Please try again in a few minutes."
        )
    
    if 'private' in error_lower or 'unavailable' in error_lower or 'not available' in error_lower:
        logger.warning("Video unavailable on %s: %s", platform, error_msg)
        return f"This {platform} video is private, deleted, or unavailable."
    
    if 'unsupported' in error_lower or 'no video' in error_lower:
        logger.warning("Unsupported content on %s: %s", platform, error_msg)
        return f"This URL doesn't contain a downloadable {platform} video."
    
    logger.error("Unclassified %s error: %s", platform, error_msg)
    return f"Could not process this {platform} video. Please check the URL and try again."


# ── yt-dlp Options Builder ────────────────────────────────────
def get_base_ydl_opts():
    """Returns the base yt-dlp options with cookie support and anti-bot headers."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://www.facebook.com/",
        "Accept-Language": "en-US,en;q=0.9"
    }

    opts = {
        'quiet': True,
        'no_warnings': True,
        'http_headers': headers,
        'socket_timeout': 30,
    }

    if os.path.exists(COOKIES_FILE):
        opts['cookiefile'] = COOKIES_FILE
    
    return opts


# ── File Cleanup ──────────────────────────────────────────────
def delete_file_delayed(filepath, delay=1800):
    """
    Background thread to delete the file after a delay (e.g., 5 minutes).
    This safely allows Flask's send_file to stream the video to the user before deletion.
    """
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
    """Periodically check and delete old files from download directory"""
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

    fb_regex = r'(https?://(?:www\.|web\.|m\.)?(facebook\.com|fb\.watch|fb\.gg)/.+)'
    if not re.match(fb_regex, video_url):
        return jsonify({"error": "Sorry, this downloader only supports Facebook videos."}), 400

    ydl_opts = get_base_ydl_opts()

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)

            raw_title = info_dict.get('title')
            description = info_dict.get('description')
            
            title = ""
            if description and len(description.strip()) > 0:
                title = " ".join(description.splitlines())[:60] + "..."
            elif raw_title and not raw_title.startswith("Video by "):
                title = raw_title
            else:
                title = "Facebook_Video"

            # Try multiple thumbnail sources
            thumbnail = ""
            if info_dict.get('thumbnail'):
                thumbnail = info_dict['thumbnail']
            elif info_dict.get('thumbnails'):
                for tb in reversed(info_dict['thumbnails']):
                    if tb.get('url'):
                        thumbnail = tb['url']
                        break
            
            # Proxy the thumbnail through our backend to bypass CORS/referrer issues
            if thumbnail:
                from urllib.parse import quote
                thumbnail = f"/api/thumb_proxy?url={quote(thumbnail, safe='')}"

            # Fixed quality tiers - always show standard options
            available_formats = [
                {"resolution": "1440p (2K)", "height": 1440},
                {"resolution": "1080p (Full HD)", "height": 1080},
                {"resolution": "720p (HD)", "height": 720},
                {"resolution": "480p (SD)", "height": 480},
            ]

            logger.info("✅ Info fetched for: %s", video_url)

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
    """Proxy thumbnail images to bypass CORS and referrer restrictions"""
    img_url = request.args.get('url', '')
    if not img_url:
        return "No URL", 400
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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

    ydl_opts = get_base_ydl_opts()
    ydl_opts.update({
        'format': f'bestvideo[height={res_height}]+bestaudio/bestvideo[height<={res_height}]+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': filepath,
    })

    try:
        logger.info("⬇️  Downloading FB: %s at %sp", video_url, res_height)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

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