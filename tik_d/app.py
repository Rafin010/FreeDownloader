import os
import uuid
import threading
import time
import re
from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp

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
            
            title = info_dict.get('title', 'TikTok_Video')
            thumbnail = info_dict.get('thumbnail', '')
            formats = info_dict.get('formats', [])
            
            # Extract unique resolutions available
            resolutions = set()
            for f in formats:
                height = f.get('height')
                if height and height >= 240: 
                    resolutions.add(height)
            
            sorted_res = sorted(list(resolutions), reverse=True)
            
            available_formats = []
            for res in sorted_res:
                available_formats.append({
                    "resolution": f"{res}p",
                    "height": res
                })

            # If yt-dlp doesn't find specific height formats for TikTok, add a default 'Best' option
            if not available_formats:
                available_formats.append({"resolution": "Watermark-free (Best)", "height": "best"})

            return jsonify({
                "title": title,
                "thumbnail": thumbnail,
                "formats": available_formats
            })

    except Exception as e:
        return jsonify({"error": f"Video might be private or invalid. (Error: {str(e)})"}), 500

@app.route('/api/download')
def download_video():
    video_url = request.args.get('url')
    res_height = request.args.get('res', 'best')

    if not video_url:
        return "URL Missing", 400

    unique_filename = f"TikTok_Video_{uuid.uuid4().hex[:8]}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, unique_filename)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.tiktok.com/"
    }

    format_str = f"bestvideo[height<={res_height}]+bestaudio/best" if res_height != 'best' else "best"

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
            return send_file(filepath, as_attachment=True)
        else:
            return "Download failed to process", 500

    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)