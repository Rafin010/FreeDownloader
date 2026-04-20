"""
Celery Application Factory — Creates Celery instances for each downloader service.

Usage:
    from infra.celery_app import make_celery
    celery = make_celery('yt_d')

Each service gets its own named Celery app and task queue to prevent
cross-contamination and allow independent scaling.
"""

import os
import logging

logger = logging.getLogger(__name__)

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Celery result backend uses DB 1 to separate from cache (DB 0)
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/1')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')


def make_celery(service_name):
    """Create a Celery app for a specific downloader service.

    Args:
        service_name: One of 'yt_d', 'tik_d', 'insta_d', 'fb_downloader', 'p_d'

    Returns:
        Configured Celery app instance
    """
    try:
        from celery import Celery
    except ImportError:
        logger.error("❌ celery package not installed. Install with: pip install celery[redis]")
        raise

    app = Celery(
        service_name,
        broker=CELERY_BROKER_URL,
        backend=CELERY_RESULT_BACKEND,
    )

    # Queue routing — each service gets its own queue
    queue_name = f"{service_name}_queue"

    app.conf.update(
        # Serialization
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',

        # Results expire after 30 minutes (matches file cleanup)
        result_expires=1800,

        # Task execution
        task_acks_late=True,                    # Ack after completion (crash-safe)
        task_reject_on_worker_lost=True,        # Re-queue if worker dies
        task_time_limit=600,                    # Hard limit: 10 minutes per task
        task_soft_time_limit=540,               # Soft limit: 9 minutes (raise SoftTimeLimitExceeded)

        # Worker
        worker_prefetch_multiplier=1,           # Don't prefetch (tasks are heavy)
        worker_max_tasks_per_child=50,          # Recycle workers to prevent memory leaks
        worker_max_memory_per_child=512_000,    # Kill worker if it uses >512MB

        # Default queue
        task_default_queue=queue_name,

        # Timezone
        timezone='UTC',
        enable_utc=True,

        # Broker connection retry
        broker_connection_retry_on_startup=True,
    )

    logger.info("✅ Celery app created: %s (queue: %s)", service_name, queue_name)
    return app


def make_celery_with_flask(service_name, flask_app):
    """Create a Celery app integrated with a Flask app context.

    This ensures Celery tasks have access to Flask's app context
    (needed for config, logging, etc.).
    """
    celery = make_celery(service_name)

    class ContextTask(celery.Task):
        """Ensure each task runs within Flask app context."""
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
