import socket
import dns.resolver
from curl_cffi import requests

# Patch DNS resolution
_original_getaddrinfo = socket.getaddrinfo
def _patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    try:
        if host in ['fastdl.app', 'snapinsta.to', 'sssinstagram.com']:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = ['8.8.8.8']
            answers = resolver.resolve(host, 'A')
            ip = answers[0].address
            # Return mocked addrinfo
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (ip, port))]
    except Exception:
        pass
    return _original_getaddrinfo(host, port, family, type, proto, flags)

socket.getaddrinfo = _patched_getaddrinfo

def test_api():
    print("\n--- Testing fastdl.app ---")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Origin': 'https://fastdl.app',
        'Referer': 'https://fastdl.app/',
        'Accept': '*/*',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    try:
        # We need to find the correct endpoint. Usually it's something like /action.php or /api/ajaxSearch.
        # Let's try to fetch the home page first to see what the form posts to.
        r = requests.get("https://fastdl.app/", headers=headers, impersonate="chrome110", timeout=10)
        print("Status:", r.status_code)
        import re
        action = re.search(r'action="([^"]+)"', r.text)
        print("Action URL found in form:", action.group(1) if action else "None")
    except Exception as e:
        print("Error:", e)

    print("\n--- Testing snapinsta.to ---")
    headers['Origin'] = 'https://snapinsta.to'
    headers['Referer'] = 'https://snapinsta.to/'
    try:
        r = requests.get("https://snapinsta.to/", headers=headers, impersonate="chrome110", timeout=10)
        print("Status:", r.status_code)
        import re
        action = re.search(r'action="([^"]+)"', r.text)
        print("Action URL found in form:", action.group(1) if action else "None")
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    test_api()
