import os
import uuid
import threading
import time
import re
from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp

# ফ্লাস্ক অ্যাপ ইনিশিয়ালাইজেশন (এটি আগে নিচে ছিল, যা একটি এরর তৈরি করতো)
app = Flask(__name__)

# সাময়িক ফাইল রাখার ফোল্ডার
DOWNLOAD_DIR = 'temp_videos'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# কতক্ষণ পর ডিলিট হবে (সেকেন্ডে) - যেমন ১০ মিনিট = ৬০০ সেকেন্ড
FILE_EXPIRY_TIME = 600 

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

def cleanup_old_files():
    """এই ফাংশনটি নির্দিষ্ট সময় পর পর ফোল্ডার চেক করে পুরনো ফাইল ডিলিট করবে"""
    while True:
        now = time.time()
        if os.path.exists(DOWNLOAD_DIR):
            for f in os.listdir(DOWNLOAD_DIR):
                file_path = os.path.join(DOWNLOAD_DIR, f)
                # ফাইলের বয়স চেক করা হচ্ছে
                if os.stat(file_path).st_mtime < now - FILE_EXPIRY_TIME:
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            print(f"Deleted old file: {f}")
                    except Exception as e:
                        print(f"Error deleting file {f}: {e}")
        
        # প্রতি ৫ মিনিট পর পর চেক করবে
        time.sleep(300) 

# ব্যাকগ্রাউন্ড থ্রেড শুরু করা যাতে মেইন অ্যাপ চলতে থাকে
cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()        

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/get_info', methods=['POST'])
def get_info():
    data = request.json
    video_url = data.get('url')

    if not video_url:
        return jsonify({"error": "No URL provided!"}), 400

    # Instagram URL Validation Regex (Supports post, reel, tv, etc.)
    ig_regex = r'(https?://(?:www\.)?instagram\.com/(?:p|reel|tv|reels)/.+)'
    if not re.match(ig_regex, video_url):
        return jsonify({"error": "Sorry, this downloader only supports Instagram videos and reels."}), 400

    # Headers to bypass 403 Forbidden errors
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.instagram.com/",
        "Accept-Language": "en-US,en;q=0.9"
    }

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'http_headers': headers,
        # 'cookiefile': 'cookies.txt' # আনকমেন্ট করুন যদি প্রাইভেট ভিডিও বা লগিন এরর আসে
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            
            title = info_dict.get('title', 'Instagram_Video')
            thumbnail = info_dict.get('thumbnail', '')
            formats = info_dict.get('formats', [])
            
            # Extract unique resolutions available
            resolutions = set()
            for f in formats:
                height = f.get('height')
                if height and height >= 240: # Filter out tiny audio-only metadata formats
                    resolutions.add(height)
            
            # Sort resolutions descending (e.g., 1080, 720, 480)
            sorted_res = sorted(list(resolutions), reverse=True)
            
            available_formats = []
            for res in sorted_res:
                available_formats.append({
                    "resolution": f"{res}p",
                    "height": res
                })

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
    res_height = request.args.get('res', '1080')

    if not video_url:
        return "URL Missing", 400

    # Generate unique UUID filename for concurrent users (Instagram specific name)
    unique_filename = f"IG_Video_{uuid.uuid4().hex[:8]}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, unique_filename)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.instagram.com/"
    }

    # Request the best video up to requested height + best audio, merge into MP4
    ydl_opts = {
        'format': f'bestvideo[height<={res_height}]+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': filepath,
        'quiet': True,
        'http_headers': headers,
        # 'cookiefile': 'cookies.txt' # আনকমেন্ট করুন যদি প্রাইভেট ভিডিও বা লগিন এরর আসে
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        # Trigger auto-delete in 5 minutes
        delete_file_delayed(filepath, delay=300)

        return send_file(
            filepath, 
            as_attachment=True, 
            download_name=unique_filename,
            mimetype='video/mp4'
        )

    except Exception as e:
        # If download fails, ensure cleanup
        if os.path.exists(filepath):
            os.remove(filepath)
        return f"Download Failed: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True, threaded=True)