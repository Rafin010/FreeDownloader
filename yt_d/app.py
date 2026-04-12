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


# ── YouTube-specific: Multiple extraction strategies ──────────
# yt-dlp 2025 uses 'player_client' in extractor_args.
# Different clients bypass different bot checks.
# We'll also try with the PO Token approach and different configs.
def build_yt_opts(strategy_idx=0):
    """Build yt-dlp options for YouTube, rotating strategies."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    # Different strategies to try
    strategies = [
        # Strategy 0: mweb client — often bypasses bot detection  
        {'youtube': {'player_client': ['mweb']}},
        # Strategy 1: tv_embedded — Smart TV client, no login needed
        {'youtube': {'player_client': ['tv_embedded']}},
        # Strategy 2: ios client
        {'youtube': {'player_client': ['ios']}},
        # Strategy 3: android client
        {'youtube': {'player_client': ['android']}},
        # Strategy 4: default (let yt-dlp decide)
        {},
    ]

    idx = strategy_idx % len(strategies)
    ext_args = strategies[idx]

    opts = {
        'quiet': True,
        'no_warnings': True,
        'http_headers': headers,
        'socket_timeout': 30,
        'force_ipv4': True,
    }
    if ext_args:
        opts['extractor_args'] = ext_args

    if os.path.exists(COOKIES_FILE):
        opts['cookiefile'] = COOKIES_FILE

    return opts, len(strategies)


def extract_with_retry(video_url):
    """Try ALL strategies. Retry on ANY error for YouTube since most are transient."""
    _, num_strategies = build_yt_opts(0)
    last_error = None

    for i in range(num_strategies):
        try:
            opts, _ = build_yt_opts(i)
            logger.info("YT strategy %d for: %s", i, video_url)
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                logger.info("✅ YT strategy %d succeeded!", i)
                return info, i
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            # For truly invalid URLs, private videos, or login-required — don't retry
            if 'is not a valid url' in error_str or 'private video' in error_str or 'login_required' in error_str:
                raise e
            logger.warning("YT strategy %d failed: %s", i, str(e)[:100])
            continue

    raise last_error


def download_with_retry(video_url, filepath, res_height):
    """Download video using multiple strategies."""
    _, num_strategies = build_yt_opts(0)
    last_error = None

    for i in range(num_strategies):
        try:
            opts, _ = build_yt_opts(i)
            opts['socket_timeout'] = 120  # Longer timeout for downloads
            opts.update({
                'format': f'bestvideo[height<={res_height}]+bestaudio/best[height<={res_height}]/best',
                'merge_output_format': 'mp4',
                'outtmpl': filepath,
            })
            logger.info("YT download strategy %d", i)
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([video_url])
            if os.path.exists(filepath):
                logger.info("✅ YT download strategy %d succeeded!", i)
                return True
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            if 'is not a valid url' in error_str or 'private video' in error_str or 'login_required' in error_str:
                raise e
            # Clean up partial file before retry
            for partial in [filepath, filepath + '.part', filepath + '.ytdl']:
                if os.path.exists(partial):
                    os.remove(partial)
            logger.warning("YT download strategy %d failed: %s", i, str(e)[:100])
            continue

    raise last_error


# ── Error Classification ──────────────────────────────────────
def classify_yt_error(error_msg):
    error_lower = error_msg.lower()
    if 'sign in' in error_lower or 'bot' in error_lower or 'confirm' in error_lower:
        return "YouTube is temporarily blocking downloads from this server. Please try again in a few minutes."
    if 'private video' in error_lower or 'video unavailable' in error_lower or 'is not available' in error_lower:
        return "This video is private, deleted, or unavailable."
    if 'age' in error_lower or 'login_required' in error_lower:
        return "This video is age-restricted."
    if 'geo' in error_lower or 'not available in your country' in error_lower:
        return "This video is not available in the server's region."
    if 'copyright' in error_lower or 'removed' in error_lower:
        return "This video has been removed due to copyright."
    if 'live' in error_lower and 'not supported' in error_lower:
        return "Live streams cannot be downloaded."
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