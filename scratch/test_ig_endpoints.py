import socket
import dns.resolver
from curl_cffi import requests
import re

_original_getaddrinfo = socket.getaddrinfo
def _patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    try:
        if host in ['fastdl.app']:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = ['8.8.8.8']
            answers = resolver.resolve(host, 'A')
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (answers[0].address, port))]
    except Exception:
        pass
    return _original_getaddrinfo(host, port, family, type, proto, flags)

socket.getaddrinfo = _patched_getaddrinfo

def test_api():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Origin': 'https://fastdl.app',
        'Referer': 'https://fastdl.app/'
    }
    r = requests.get("https://fastdl.app/", headers=headers, impersonate="chrome110", timeout=10)
    
    # find all URLs or endpoints in the html
    endpoints = re.findall(r'[\'"](/api/[^\'"]+|/ajax/[^\'"]+|https?://[^\'"]*api[^\'"]*)[\'"]', r.text)
    print("Found endpoints:", endpoints)
    
    scripts = re.findall(r'<script[^>]*src="([^"]+)"', r.text)
    for s in scripts:
        if s.startswith('/'):
            s = "https://fastdl.app" + s
        try:
            print(f"Fetching JS: {s}")
            r2 = requests.get(s, headers=headers, impersonate="chrome110", timeout=10)
            js_endpoints = re.findall(r'[\'"](/api/[^\'"]+|/ajax/[^\'"]+|/action\.php|https?://[^\'"]*api[^\'"]*)[\'"]', r2.text)
            if js_endpoints:
                print(f"  Found in JS: {set(js_endpoints)}")
        except Exception as e:
            print("  Failed:", e)

if __name__ == '__main__':
    test_api()
