"""
Unified WSGI Application — Port-based Dispatcher

একটি মাত্র gunicorn প্রসেস, সব সার্ভিস আলাদা পোর্টে।
প্রথম রিকোয়েস্ট পর্যন্ত প্রতিটি sub-app লেজিলোড (মেমরি বাঁচায়)।
"""
import sys
import os
import logging

_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger('unified')

PORT_MAP = {
    '8004': ('yt_d.app',         'app'),   # y.freedownloader.top
    '8001': ('fb_downloader.app','app'),   # f.freedownloader.top
    '8002': ('insta_d.app',      'app'),   # i.freedownloader.top
    '8003': ('tik_d.app',        'app'),   # t.freedownloader.top
    '8009': ('p_d.app',          'app'),   # p.freedownloader.top
    '5000': ('backend.app',      'app'),   # admin.freedownloader.top
    '8010': ('freeStore.app',    'app'),   # freedownloader.top
    '5007': ('freeStore.app',    'app'),   # donate.freedownloader.top
    '8008': ('free_d.app',       'app'),   # web.freedownloader.top
}

HOST_MAP = {
    'y.freedownloader.top':       '8004',
    'f.freedownloader.top':       '8001',
    'i.freedownloader.top':       '8002',
    't.freedownloader.top':       '8003',
    'p.freedownloader.top':       '8009',
    'admin.freedownloader.top':   '5000',
    'donate.freedownloader.top':  '5007',
    'web.freedownloader.top':     '8008',
    'freedownloader.top':         '8010',
    'www.freedownloader.top':     '8010',
    'store.freedownloader.top':   '8010',
}

_app_cache = {}

def _get_app(module_path, attr_name):
    key = f'{module_path}:{attr_name}'
    if key not in _app_cache:
        logger.info('Lazy-loading: %s', module_path)
        import importlib
        mod = importlib.import_module(module_path)
        _app_cache[key] = getattr(mod, attr_name)
    return _app_cache[key]


def application(environ, start_response):
    port = environ.get('SERVER_PORT', '')
    host = environ.get('HTTP_HOST', '').split(':')[0].lower()

    # Primary: route by port
    if port in PORT_MAP:
        module_path, attr = PORT_MAP[port]
        app = _get_app(module_path, attr)
        return app(environ, start_response)

    # Fallback: route by host (for direct access without port routing)
    if host in HOST_MAP:
        port = HOST_MAP[host]
        if port in PORT_MAP:
            module_path, attr = PORT_MAP[port]
            app = _get_app(module_path, attr)
            return app(environ, start_response)

    logger.warning('Unknown host/port: %s:%s', host, port)
    start_response('404 Not Found', [('Content-Type', 'text/plain')])
    return [b'Not Found']
