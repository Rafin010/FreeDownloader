import socket
import dns.resolver
from curl_cffi import requests

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

def dump_html():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Origin': 'https://fastdl.app',
        'Referer': 'https://fastdl.app/'
    }
    r = requests.get("https://fastdl.app/", headers=headers, impersonate="chrome110", timeout=10)
    with open('e:\\_free downloader Projext\\scratch\\fastdl.html', 'w', encoding='utf-8') as f:
        f.write(r.text)
    print("Dumped fastdl.html")

if __name__ == '__main__':
    dump_html()
