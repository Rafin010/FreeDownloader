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

FILE_EXPIRY_TIME = 1800 


# ── Cookie Validation ─────────────────────────────────────────
def validate_cookies():
    """
    Check if cookies.txt exists and contains authenticated YouTube cookies.
    Logs clear warnings if cookies are missing or appear to be anonymous-only.
    """
    if not os.path.exists(COOKIES_FILE):
        logger.warning(
            "⚠️  cookies.txt NOT FOUND at: %s\n"
            "   YouTube will likely block requests with 'Sign in to confirm you're not a bot'.\n"
            "   → Export cookies from a logged-in YouTube browser session.\n"
            "   → See deployment instructions for details.",
            COOKIES_FILE
        )
        return False

    try:
        with open(COOKIES_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # These cookies indicate an authenticated Google/YouTube session
        auth_markers = ['LOGIN_INFO', 'SID', 'SSID', '__Secure-1PSID', '__Secure-3PSID']
        found = [m for m in auth_markers if m in content]
        
        if not found:
            logger.warning(
                "⚠️  cookies.txt exists but contains NO authenticated session cookies.\n"
                "   Found file at: %s\n"
                "   Missing markers: %s\n"
                "   → The file likely contains only anonymous visitor cookies (useless for bot bypass).\n"
                "   → Re-export cookies while LOGGED INTO YouTube with a Google account.",
                COOKIES_FILE, ', '.join(auth_markers)
            )
            return False
        
        logger.info(
            "✅ cookies.txt loaded with authenticated session (found: %s)",
            ', '.join(found)
        )
        return True
    except Exception as e:
        logger.error("❌ Failed to read cookies.txt: %s", e)
        return False

# Run validation on startup
_cookies_valid = validate_cookies()


# ── Error Classification ──────────────────────────────────────
def classify_yt_error(error_msg):
    """
    Classify a yt-dlp error into a user-friendly message and log category.
    Returns (user_message, log_level).
    """
    error_lower = error_msg.lower()
    
    # Bot / sign-in block
    if 'sign in to confirm' in error_lower or 'bot' in error_lower:
        logger.error(
            "🚫 BOT BLOCK DETECTED — YouTube requires sign-in.\n"
            "   Raw error: %s\n"
            "   → Check if cookies.txt contains valid, non-expired authenticated cookies.\n"
            "   → Re-export cookies from a freshly logged-in browser session.",
            error_msg
        )
        return (
            "YouTube is temporarily blocking our server due to high traffic. "
            "Please try again in a few minutes. If the issue persists, the server admin "
            "needs to refresh the authentication cookies."
        )
    
    # Private / unavailable
    if 'private video' in error_lower or 'video unavailable' in error_lower or 'is not available' in error_lower:
        logger.warning("Video unavailable: %s", error_msg)
        return "This video is private, deleted, or unavailable. Please check the URL."
    
    # Age restriction / login required
    if 'age' in error_lower or 'login_required' in error_lower or 'age-restricted' in error_lower:
        logger.warning("Age/login restricted: %s", error_msg)
        return "This video is age-restricted or requires sign-in to view."
    
    # Geographic restriction
    if 'geo' in error_lower or 'not available in your country' in error_lower:
        logger.warning("Geo-restricted: %s", error_msg)
        return "This video is not available in the server's region."
    
    # Copyright / takedown
    if 'copyright' in error_lower or 'removed' in error_lower or 'terminated' in error_lower:
        logger.warning("Copyright/removed: %s", error_msg)
        return "This video has been removed due to copyright or a Terms of Service violation."

    # Live stream
    if 'live' in error_lower and 'not supported' in error_lower:
        logger.warning("Live stream: %s", error_msg)
        return "Live streams cannot be downloaded. Please wait until the stream ends."
    
    # Fallback
    logger.error("Unclassified yt-dlp error: %s", error_msg)
    return "Could not process this video. Please check the URL and try again."


# ── yt-dlp Options Builder ────────────────────────────────────
def get_base_ydl_opts():
    """
    Returns the base yt-dlp options shared across info extraction and downloading.
    Includes cookie support, anti-bot headers, and throttling.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://www.youtube.com/",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    opts = {
        'quiet': True,
        'no_warnings': True,
        'http_headers': headers,
        'socket_timeout': 30,
        # Throttle requests to reduce bot detection
        'sleep_interval': 1,
        'max_sleep_interval': 3,
        # Use the web client player for better compatibility
        'extractor_args': {'youtube': {'player_client': ['web']}},
    }

    # Only add cookiefile if the file actually exists
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
                if os.stat(file_path).st_mtime < now - FILE_EXPIRY_TIME:
                    try:
                        if os.path.isfile(file_path):
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

    yt_regex = r'(https?://(?:www\.)?(?:youtube\.com|youtu\.be)/.+)'
    if not re.match(yt_regex, video_url):
        return jsonify({"error": "Sorry, this downloader only supports YouTube videos and Shorts."}), 400

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
                title = "YouTube_Video"

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
        user_message = classify_yt_error(error_msg)
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
    res_height = request.args.get('res', '1080')
    req_title = request.args.get('title', 'YouTube_Video')

    if not video_url:
        return "URL Missing", 400

    # Clean the title of invalid filename characters to avoid issues across OS
    safe_title = re.sub(r'[\\/*?:"<>|]', "", req_title).strip()
    if not safe_title:
        safe_title = "YouTube_Video"

    # Generate UUID filename for the server (safe concurrent processing)
    # But we will use safe_title for the user's downloaded file
    unique_filename = f"YT_Video_{uuid.uuid4().hex[:8]}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, unique_filename)
    user_download_name = f"{safe_title}.mp4"

    ydl_opts = get_base_ydl_opts()
    ydl_opts.update({
        # Select exact resolution or fallback to the closest best below it
        'format': f'bestvideo[height={res_height}]+bestaudio/bestvideo[height<={res_height}]+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': filepath,
    })

    try:
        logger.info("⬇️  Downloading: %s at %sp", video_url, res_height)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        # Trigger auto-delete in 5 minutes
        delete_file_delayed(filepath, delay=1800)

        logger.info("✅ Download complete: %s", unique_filename)

        response = make_response(send_file(
            filepath, 
            as_attachment=True, 
            download_name=user_download_name,
            mimetype='video/mp4'
        ))
        # কুকি সেট করা হলো যা ফ্রন্টএন্ড থেকে পোল করা হবে
        response.set_cookie('download_status', 'completed', path='/')
        return response

    except Exception as e:
        import traceback
        traceback.print_exc()

        # If download fails, ensure cleanup
        if os.path.exists(filepath):
            os.remove(filepath)
        
        error_msg = str(e)
        user_message = classify_yt_error(error_msg)
        return jsonify({"error": user_message}), 500

if __name__ == '__main__':
    app.run(debug=True, threaded=True)