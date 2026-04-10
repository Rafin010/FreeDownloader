import os
import uuid
import threading
import time
import re
from flask import Flask, render_template, request, jsonify, send_file, Response
import yt_dlp
import requests as http_requests

app = Flask(__name__)

# Ensure download directory exists
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def delete_file_delayed(filepath, delay=300):
    """
    Background thread to delete the file after a delay (e.g., 5 minutes).
    This safely allows Flask's send_file to stream the video to the user before deletion.
    """
    def task():
        time.sleep(delay)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"Auto-deleted: {filepath}")
        except Exception as e:
            print(f"Error deleting file {filepath}: {e}")
            
    threading.Thread(target=task, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/get_info', methods=['POST'])
def get_info():
    data = request.json
    video_url = data.get('url')

    if not video_url:
        return jsonify({"error": "No URL provided!"}), 400

    # Updated Regex for TikTok URLs
    tiktok_regex = r'(https?://(?:www\.|vm\.|vt\.)?tiktok\.com/.+)'
    if not re.match(tiktok_regex, video_url):
        return jsonify({"error": "Sorry, this downloader only supports TikTok videos."}), 400

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.tiktok.com/",
        "Accept-Language": "en-US,en;q=0.9"
    }

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'http_headers': headers,
    }

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
                title = "TikTok_Video"

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

            formats = info_dict.get('formats', [])
            
            # Check if any video format with height info exists
            has_height = any(f.get('height') for f in formats if f.get('height'))
            
            if has_height:
                # Fixed quality tiers - always show standard options
                available_formats = [
                    {"resolution": "1440p (2K)", "height": 1440},
                    {"resolution": "1080p (Full HD)", "height": 1080},
                    {"resolution": "720p (HD)", "height": 720},
                    {"resolution": "480p (SD)", "height": 480},
                ]
            else:
                # If yt-dlp doesn't find specific height formats for TikTok, add a default 'Best' option
                available_formats = [{"resolution": "Watermark-free (Best)", "height": "best"}]

            return jsonify({
                "title": title,
                "thumbnail": thumbnail,
                "formats": available_formats
            })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Video might be private or invalid. (Error: {str(e)})"}), 500

@app.route('/api/thumb_proxy')
def thumb_proxy():
    """Proxy thumbnail images to bypass CORS and referrer restrictions"""
    img_url = request.args.get('url', '')
    if not img_url:
        return "No URL", 400
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
    res_height = request.args.get('res', 'best')
    req_title = request.args.get('title', 'TikTok_Video')

    if not video_url:
        return "URL Missing", 400

    safe_title = re.sub(r'[\\/*?:"<>|]', "", req_title).strip()
    if not safe_title:
        safe_title = "TikTok_Video"

    unique_filename = f"TikTok_Video_{uuid.uuid4().hex[:8]}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, unique_filename)
    user_download_name = f"{safe_title}.mp4"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.tiktok.com/"
    }

    format_str = f"bestvideo[height={res_height}]+bestaudio/bestvideo[height<={res_height}]+bestaudio/best" if res_height != 'best' else "best"

    ydl_opts = {
        'format': format_str,
        'outtmpl': filepath,
        'quiet': True,
        'http_headers': headers,
        'merge_output_format': 'mp4'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        if os.path.exists(filepath):
            delete_file_delayed(filepath, delay=300) # Delete after 5 mins
            return send_file(filepath, as_attachment=True, download_name=user_download_name, mimetype='video/mp4')
        else:
            return "Download failed to process", 500

    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)