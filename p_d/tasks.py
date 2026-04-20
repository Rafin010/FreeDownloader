"""
P_D Celery Tasks — Async extraction and download workers.

Run the worker with:
    cd /root/FreeDownloader/p_d
    celery -A tasks worker --concurrency=8 --pool=prefork -Q p_d_queue --loglevel=info
"""

import os
import sys
import uuid
import re
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infra.celery_app import make_celery
from infra.progress import update_progress
from infra.redis_client import cache_get, cache_set

logger = logging.getLogger(__name__)
celery = make_celery('p_d')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, 'downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def _get_app_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location("pd_app", os.path.join(BASE_DIR, 'app.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@celery.task(bind=True, name='pd.download_video', max_retries=1)
def celery_download_pd(self, video_url, res_height, title):
    task_id = self.request.id
    safe_title = re.sub(r'[\\/*?:"<>|]', "", title).strip() or "Video"
    unique_filename = f"PD_Video_{uuid.uuid4().hex[:8]}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, unique_filename)
    user_download_name = f"{safe_title}.mp4"

    try:
        update_progress(task_id, 'extracting', 10, 'Preparing download...',
                        download_name=user_download_name)

        app_mod = _get_app_module()

        update_progress(task_id, 'downloading', 30, 'Downloading video...',
                        download_name=user_download_name)

        app_mod.download_with_retry(video_url, filepath, res_height)

        if not os.path.exists(filepath):
            raise FileNotFoundError("Download completed but file not found")

        app_mod.delete_file_delayed(filepath, delay=1800)
        file_size = os.path.getsize(filepath)

        update_progress(task_id, 'ready', 100,
                        f'Download ready ({file_size // (1024*1024)}MB)',
                        filepath=filepath, download_name=user_download_name)

        return {'filepath': filepath, 'download_name': user_download_name, 'file_size': file_size}

    except Exception as e:
        if os.path.exists(filepath):
            try: os.remove(filepath)
            except OSError: pass
        app_mod = _get_app_module()
        user_message = app_mod.classify_download_error(str(e), "Video")
        update_progress(task_id, 'error', 0, user_message, error=user_message,
                        download_name=user_download_name)
        raise
