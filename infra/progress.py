"""
Task Progress Tracking — Real-time progress updates via Redis.

Usage (in Celery tasks):
    from infra.progress import update_progress, get_progress

    update_progress(task_id, 'downloading', percent=45, message='Downloading video...')

Usage (in Flask routes):
    progress = get_progress(task_id)
    # Returns: {'stage': 'downloading', 'percent': 45, 'message': '...', 'filepath': None}

Stages: queued → extracting → downloading → merging → ready → error → expired
"""

import json
import logging

from infra.redis_client import get_redis

logger = logging.getLogger(__name__)

# Progress data expires after 30 minutes (matches file cleanup)
PROGRESS_TTL = 1800

# Valid stages in order
STAGES = ['queued', 'extracting', 'downloading', 'merging', 'ready', 'error', 'expired']


def _progress_key(task_id):
    """Redis key for task progress."""
    return f"fd:progress:{task_id}"


def update_progress(task_id, stage, percent=0, message='', filepath=None, download_name=None, error=None):
    """Update task progress in Redis.

    Args:
        task_id: Celery task ID
        stage: One of STAGES
        percent: 0-100 progress percentage
        message: Human-readable status message
        filepath: Path to completed file (set when stage='ready')
        download_name: User-facing filename for download
        error: Error message (set when stage='error')
    """
    r = get_redis()
    if not r:
        return False

    try:
        data = {
            'task_id': task_id,
            'stage': stage,
            'percent': min(max(int(percent), 0), 100),
            'message': message,
            'filepath': filepath,
            'download_name': download_name,
            'error': error,
        }
        key = _progress_key(task_id)
        r.setex(key, PROGRESS_TTL, json.dumps(data))
        logger.debug("📊 Progress [%s]: %s %d%% — %s", task_id[:8], stage, percent, message)
        return True
    except Exception as e:
        logger.warning("Progress update error: %s", str(e)[:80])
        return False


def get_progress(task_id):
    """Get current task progress from Redis.

    Returns dict with keys: task_id, stage, percent, message, filepath, download_name, error
    Returns a 'queued' status if no progress data exists yet.
    """
    r = get_redis()
    if not r:
        return {
            'task_id': task_id,
            'stage': 'error',
            'percent': 0,
            'message': 'Progress tracking unavailable (Redis not connected)',
            'filepath': None,
            'download_name': None,
            'error': 'Redis unavailable',
        }

    try:
        key = _progress_key(task_id)
        data = r.get(key)
        if data:
            return json.loads(data)
        # No progress yet — task is queued
        return {
            'task_id': task_id,
            'stage': 'queued',
            'percent': 0,
            'message': 'Waiting in queue...',
            'filepath': None,
            'download_name': None,
            'error': None,
        }
    except Exception as e:
        logger.warning("Progress get error: %s", str(e)[:80])
        return {
            'task_id': task_id,
            'stage': 'error',
            'percent': 0,
            'message': 'Could not retrieve progress',
            'filepath': None,
            'download_name': None,
            'error': str(e),
        }


def delete_progress(task_id):
    """Delete progress data for a completed/expired task."""
    r = get_redis()
    if not r:
        return False
    try:
        r.delete(_progress_key(task_id))
        return True
    except Exception:
        return False
