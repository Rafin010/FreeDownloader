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

FILE_EXPIRY_TIME = 1800  # 30 minutes


# ── TikTok-specific strategies ────────────────────────────────
# TikTok blocks certain API endpoints. We rotate between
# different extractor args and User-Agents.
def build_tiktok_opts(strategy_idx=0):
    """Build yt-dlp options for TikTok with different strategies."""
    
    user_agents = [
        # Mobile UA (best for TikTok)
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        # Android 
        "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        # Desktop Chrome
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    ]

    # Different TikTok API hostnames to try
    tiktok_strategies = [
        # Strategy 0: Use api22 hostname (often works when default fails)
        {'tiktok': {'api_hostname': ['api22-normal-c-useast2a.tiktokv.com']}},
        # Strategy 1: Use api19 hostname
        {'tiktok': {'api_hostname': ['api19-normal-c-useast1a.tiktokv.com']}},
        # Strategy 2: Use api16
        {'tiktok': {'api_hostname': ['api16-normal-c-useast1a.tiktokv.com']}},
        # Strategy 3: Default (let yt-dlp decide)
        {},
    ]

    idx = strategy_idx % len(tiktok_strategies)
    ua_idx = strategy_idx % len(user_agents)

    headers = {
        "User-Agent": user_agents[ua_idx],
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.tiktok.com/",
    }

    opts = {
        'quiet': True,
        'no_warnings': True,
        'http_headers': headers,
        'socket_timeout': 30,
        'force_ipv4': True,
    }
    
    ext_args = tiktok_strategies[idx]
    if ext_args:
        opts['extractor_args'] = ext_args

    if os.path.exists(COOKIES_FILE):
        opts['cookiefile'] = COOKIES_FILE

    return opts, len(tiktok_strategies)


def extract_with_retry(video_url):
    """Try ALL strategies for TikTok extraction."""
    _, num_strategies = build_tiktok_opts(0)
    last_error = None

    for i in range(num_strategies):
        try:
            opts, _ = build_tiktok_opts(i)
            logger.info("TikTok strategy %d for: %s", i, video_url)
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                logger.info("✅ TikTok strategy %d succeeded!", i)
                return info, i
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            # Don't retry for truly invalid URLs
            if 'is not a valid url' in error_str:
                raise e
            logger.warning("TikTok strategy %d failed: %s", i, str(e)[:120])
            continue

    raise last_error


def download_with_retry(video_url, filepath, format_str):
    """Download TikTok video with retry across strategies."""
    _, num_strategies = build_tiktok_opts(0)
    last_error = None

    for i in range(num_strategies):
        try:
            opts, _ = build_tiktok_opts(i)
            opts['socket_timeout'] = 120  # Longer timeout for downloads
            opts.update({
                'format': format_str,
                'outtmpl': filepath,
                'merge_output_format': 'mp4',
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
            logger.warning("TikTok download strategy %d failed: %s", i, str(e)[:120])
            continue

    raise last_error


# ── Error Classification ──────────────────────────────────────
def classify_download_error(error_msg, platform="TikTok"):
    error_lower = error_msg.lower()
    if 'sign in' in error_lower or 'bot' in error_lower or 'captcha' in error_lower:
        return f"{platform} is temporarily blocking downloads. Please try again in a few minutes."
    if 'private' in error_lower or 'unavailable' in error_lower or 'not available' in error_lower or 'status code 0' in error_lower:
        return f"This {platform} video may be private, deleted, or region-restricted. Please try a different video."
    if 'unsupported' in error_lower or 'no video' in error_lower:
        return f"This URL doesn't contain a downloadable {platform} video."
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

    tiktok_regex = r'(https?://(?:www\.|vm\.|vt\.)?tiktok\.com/.+)'
    if not re.match(tiktok_regex, video_url):
        return jsonify({"error": "Sorry, this downloader only supports TikTok videos."}), 400

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
            title = "TikTok_Video"

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
        user_message = classify_download_error(error_msg, "TikTok")
        return jsonify({"error": user_message}), 500


@app.route('/api/thumb_proxy')
def thumb_proxy():
    img_url = request.args.get('url', '')
    if not img_url:
        return "No URL", 400
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.tiktok.com/"
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
    req_title = request.args.get('title', 'TikTok_Video')

    if not video_url:
        return "URL Missing", 400

    safe_title = re.sub(r'[\\/*?:"<>|]', "", req_title).strip()
    if not safe_title:
        safe_title = "TikTok_Video"

    unique_filename = f"TikTok_Video_{uuid.uuid4().hex[:8]}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, unique_filename)
    user_download_name = f"{safe_title}.mp4"

    format_str = f"bestvideo[height<={res_height}]+bestaudio/best[height<={res_height}]/best"

    try:
        logger.info("⬇️  Downloading TikTok: %s at %s", video_url, res_height)
        download_with_retry(video_url, filepath, format_str)

        if os.path.exists(filepath):
            delete_file_delayed(filepath, delay=1800)
            logger.info("✅ Download complete: %s", unique_filename)
            return send_file(filepath, as_attachment=True, download_name=user_download_name, mimetype='video/mp4')
        else:
            return jsonify({"error": "Download failed to process."}), 500

    except Exception as e:
        import traceback
        traceback.print_exc()
        if os.path.exists(filepath):
            os.remove(filepath)
        error_msg = str(e)
        user_message = classify_download_error(error_msg, "TikTok")
        return jsonify({"error": user_message}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)