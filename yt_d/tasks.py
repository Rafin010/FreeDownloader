"""
YouTube Celery Tasks — Async extraction and download workers.

Run the worker with:
    cd /root/FreeDownloader/yt_d
    celery -A tasks worker --concurrency=16 --pool=prefork -Q yt_d_queue --loglevel=info

Tasks:
    - celery_extract_yt: Extract video info (with Redis caching)
    - celery_download_yt: Download video file (with progress updates)
"""

import os
import sys
import uuid
import time
import re
import logging

# Add parent dir to path so we can import infra
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infra.celery_app import make_celery
from infra.progress import update_progress
from infra.redis_client import cache_get, cache_set
from infra.proxy_pool import get_proxy, mark_bad

logger = logging.getLogger(__name__)

# Create Celery app for YouTube
celery = make_celery('yt_d')

# ── Paths ──────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, 'downloads')
COOKIES_FILE = os.path.join(BASE_DIR, 'cookies.txt')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# ── Import the extraction/download logic from app.py ──────────
# We import the heavy functions rather than duplicating them.
# This is safe because Celery workers run in separate processes.
def _get_app_module():
    """Lazy import app module to avoid circular imports."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("yt_app", os.path.join(BASE_DIR, 'app.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@celery.task(bind=True, name='yt.extract_info', max_retries=2)
def celery_extract_yt(self, video_url):
    """Extract YouTube video info (async).

    Returns cached result if available, otherwise extracts fresh.
    """
    task_id = self.request.id

    try:
        update_progress(task_id, 'extracting', 10, 'Checking cache...')

        # Check Redis cache first
        cached = cache_get('yt_info', video_url)
        if cached:
            update_progress(task_id, 'ready', 100, 'Video info retrieved (cached)')
            return cached

        update_progress(task_id, 'extracting', 30, 'Extracting video information...')

        # Import app module for extraction logic
        app_mod = _get_app_module()
        info_dict, strategy_idx = app_mod.extract_with_retry(video_url)

        # Build response (same logic as get_info route)
        raw_title = info_dict.get('title')
        description = info_dict.get('description')
        duration = info_dict.get('duration', 0)
        view_count = info_dict.get('view_count', 0)
        uploader = info_dict.get('uploader', 'Unknown Channel')

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

        formats = info_dict.get('formats', [])
        
        video_audio = {}
        video_no_audio = {}
        audio_only = {}

        def format_size(size_bytes):
            if not size_bytes:
                return "Unknown"
            if size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            return f"{size_bytes / (1024 * 1024):.1f} MB"

        for f in formats:
            vcodec = f.get('vcodec')
            acodec = f.get('acodec')
            height = f.get('height')
            ext = f.get('ext')
            size = f.get('filesize') or f.get('filesize_approx') or 0
            
            # Formats object
            fmt_obj = {
                'format_id': f.get('format_id'),
                'ext': ext,
                'height': height,
                'size_bytes': size,
                'size_str': format_size(size)
            }

            if vcodec != 'none' and acodec != 'none':
                # Video + Audio
                if height and (height not in video_audio or video_audio[height]['size_bytes'] < size):
                    video_audio[height] = fmt_obj
            elif vcodec != 'none' and acodec == 'none':
                # Video No Audio
                if height and (height not in video_no_audio or video_no_audio[height]['size_bytes'] < size):
                    video_no_audio[height] = fmt_obj
            elif vcodec == 'none' and acodec != 'none':
                # Audio Only
                abr = f.get('abr') or 0
                if abr and (abr not in audio_only or audio_only[abr]['size_bytes'] < size):
                    fmt_obj['abr'] = abr
                    audio_only[abr] = fmt_obj

        # Sort and format output arrays
        va_list = sorted(video_audio.values(), key=lambda x: x['height'], reverse=True)
        vn_list = sorted(video_no_audio.values(), key=lambda x: x['height'], reverse=True)
        ao_list = sorted(audio_only.values(), key=lambda x: x.get('abr', 0), reverse=True)

        result = {
            "title": title,
            "thumbnail": thumbnail,
            "duration": duration,
            "view_count": view_count,
            "uploader": uploader,
            "formats": {
                "video_audio": va_list,
                "video_no_audio": vn_list,
                "audio_only": ao_list
            }
        }

        # Cache for 10 minutes
        cache_set('yt_info', video_url, result, ttl=600)

        update_progress(task_id, 'ready', 100, 'Video info extracted')
        return result

    except Exception as e:
        error_msg = str(e)
        update_progress(task_id, 'error', 0, error_msg, error=error_msg)
        raise


@celery.task(bind=True, name='yt.download_video', max_retries=1)
def celery_download_yt(self, video_url, res_height, title):
    """Download a YouTube video (async with progress updates).

    Returns:
        dict with 'filepath' and 'download_name' on success.
    """
    task_id = self.request.id
    res_height = str(res_height)

    # Sanitize title
    safe_title = re.sub(r'[\\/*?:"<>|]', "", title).strip()
    if not safe_title:
        safe_title = "YouTube_Video"

    unique_filename = f"YT_Video_{uuid.uuid4().hex[:8]}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, unique_filename)
    user_download_name = f"{safe_title}.mp4"

    try:
        update_progress(task_id, 'extracting', 10, 'Preparing download...',
                        download_name=user_download_name)

        # Import app module
        app_mod = _get_app_module()

        update_progress(task_id, 'downloading', 30, 'Downloading video...',
                        download_name=user_download_name)

        # Try standard yt-dlp download with retry
        try:
            app_mod.download_with_retry(video_url, filepath, res_height)
        except Exception as dl_err:
            update_progress(task_id, 'downloading', 50, 'Trying fallback...',
                            download_name=user_download_name)
            # If yt-dlp download fails, try API fallback
            logger.warning("yt-dlp download failed, trying API fallback: %s", str(dl_err)[:100])
            api_info = app_mod.extract_via_invidious_api(video_url)
            if api_info and app_mod.download_via_direct_url(api_info, filepath, res_height):
                logger.info("✅ Downloaded via API fallback direct URL")
            else:
                raise dl_err

        if not os.path.exists(filepath):
            raise FileNotFoundError("Download completed but file not found")

        # Schedule cleanup
        app_mod.delete_file_delayed(filepath, delay=1800)

        file_size = os.path.getsize(filepath)
        logger.info("✅ Celery download complete: %s (%d bytes)", unique_filename, file_size)

        update_progress(
            task_id, 'ready', 100,
            f'Download ready ({file_size // (1024*1024)}MB)',
            filepath=filepath,
            download_name=user_download_name
        )

        return {
            'filepath': filepath,
            'download_name': user_download_name,
            'file_size': file_size,
        }

    except Exception as e:
        # Clean up partial file
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass

        error_msg = str(e)
        app_mod = _get_app_module()
        user_message = app_mod.classify_yt_error(error_msg)

        update_progress(task_id, 'error', 0, user_message, error=user_message,
                        download_name=user_download_name)
        raise
