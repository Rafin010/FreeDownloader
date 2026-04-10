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

FILE_EXPIRY_TIME = 600  # 10 minutes


# ── Utility: Get Platform Name ─────────────────────────────────
def get_platform_name(url):
    """Extracts domain name from URL for dynamic logging and user messages."""
    try:
        domain = urlparse(url).netloc
        domain = domain.replace('www.', '').split('.')[0].capitalize()
        return domain if domain else "Website"
    except:
        return "Website"


# ── Cookie Validation ─────────────────────────────────────────
def validate_cookies():
    """Check if cookies.txt exists and log status on startup."""
    if not os.path.exists(COOKIES_FILE):
        logger.info(
            "ℹ️  No cookies.txt found at: %s — Downloads will work without cookies for public videos.",
            COOKIES_FILE
        )
        return False
    logger.info("✅ cookies.txt found at: %s", COOKIES_FILE)
    return True

_cookies_valid = validate_cookies()


# ── Error Classification ──────────────────────────────────────
def classify_download_error(error_msg, platform="Website"):
    """Classify a yt-dlp error into a user-friendly message."""
    error_lower = error_msg.lower()
    
    if 'sign in' in error_lower or 'bot' in error_lower or 'login' in error_lower:
        logger.error("🚫 Auth/bot block on %s: %s", platform, error_msg)
        return (
            f"{platform} is restricting access requiring a login or detecting a bot. "
            "Cookies might be expired or required for this video."
        )
    
    if 'private' in error_lower or 'unavailable' in error_lower or 'not available' in error_lower:
        logger.warning("Video unavailable on %s: %s", platform, error_msg)
        return f"This {platform} video is private, deleted, or region-restricted."
    
    if 'unsupported' in error_lower or 'no video' in error_lower:
        logger.warning("Unsupported content on %s: %s", platform, error_msg)
        return f"This URL doesn't contain a downloadable video or the platform is not supported."
    
    logger.error("Unclassified %s error: %s", platform, error_msg)
    return f"Could not process this video from {platform}. It might be protected or invalid."


# ── yt-dlp Options Builder ────────────────────────────────────
def get_base_ydl_opts():
    """Returns the base yt-dlp options with cookie support and strong anti-bot features."""
    
    opts = {
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 30,
        # POWERFUL BYPASS: Instructs yt-dlp to impersonate a real browser TLS fingerprint
        'impersonate': 'chrome', 
    }

    if os.path.exists(COOKIES_FILE):
        opts['cookiefile'] = COOKIES_FILE
    
    return opts


# ── File Cleanup ──────────────────────────────────────────────
def delete_file_delayed(filepath, delay=300):
    """Background thread to delete the file after a delay."""
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
    """Periodically check and delete old files from download directory."""
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

    # Removed the Facebook-only restriction to make it Universal
    if not video_url.startswith("http"):
        return jsonify({"error": "Invalid URL format."}), 400

    platform = get_platform_name(video_url)
    ydl_opts = get_base_ydl_opts()

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)

            raw_title = info_dict.get('title')
            description = info_dict.get('description')
            
            title = ""
            if raw_title:
                title = raw_title
            elif description and len(description.strip()) > 0:
                title = " ".join(description.splitlines())[:60] + "..."
            else:
                title = f"{platform}_Video"

            # Try multiple thumbnail sources
            thumbnail = ""
            if info_dict.get('thumbnail'):
                thumbnail = info_dict['thumbnail']
            elif info_dict.get('thumbnails'):
                for tb in reversed(info_dict['thumbnails']):
                    if tb.get('url'):
                        thumbnail = tb['url']
                        break
            
            # Proxy the thumbnail through our backend with dynamic referer
            if thumbnail:
                thumbnail = f"/api/thumb_proxy?url={quote(thumbnail, safe='')}&referer={quote(video_url, safe='')}"

            # Dynamically fetch available formats instead of hardcoding
            available_formats = []
            formats_processed = set()
            
            if 'formats' in info_dict:
                for f in info_dict['formats']:
                    # Filter for decent video formats with height
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
                
                # Sort highest quality first
                available_formats = sorted(available_formats, key=lambda k: k['height'], reverse=True)
            
            # Fallback if specific formats aren't detected well by yt-dlp for a random site
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
    """Proxy thumbnail images to bypass CORS and referrer restrictions dynamically"""
    img_url = request.args.get('url', '')
    referer_url = request.args.get('referer', 'https://google.com/')
    
    if not img_url:
        return "No URL", 400
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
    req_title = request.args.get('title', 'Universal_Video')

    if not video_url:
        return "URL Missing", 400

    platform = get_platform_name(video_url)
    
    # Create safe filename
    safe_title = re.sub(r'[\\/*?:"<>|]', "", req_title).strip()
    if not safe_title:
        safe_title = f"{platform}_Video"

    unique_filename = f"{platform}_{uuid.uuid4().hex[:8]}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, unique_filename)
    user_download_name = f"{safe_title}.mp4"

    ydl_opts = get_base_ydl_opts()
    
    # Handle the 'best' string fallback for unknown sites
    if res_height == 'best':
        format_string = 'bestvideo+bestaudio/best'
    else:
        format_string = f'bestvideo[height={res_height}]+bestaudio/bestvideo[height<={res_height}]+bestaudio/best'

    ydl_opts.update({
        'format': format_string,
        'merge_output_format': 'mp4',
        'outtmpl': filepath,
    })

    try:
        logger.info("⬇️  Downloading %s: %s at %sp", platform, video_url, res_height)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        delete_file_delayed(filepath, delay=300)

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