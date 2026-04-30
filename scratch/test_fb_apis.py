import urllib.request
import urllib.parse
import json

def test_publer(url):
    print(f"\n--- Publer API ---")
    payload = {'url': url}
    api_url = "https://app.publer.io/api/v1/provider/tools/media/extract"
    req = urllib.request.Request(api_url, data=json.dumps(payload).encode('utf-8'), headers={
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print("SUCCESS:", resp.read().decode()[:200])
    except Exception as e:
        if hasattr(e, 'read'):
            print("ERROR BODY:", e.read().decode()[:200])
        else:
            print("ERROR:", e)

def test_fdownloader(url):
    print(f"\n--- FDownloader API ---")
    data = urllib.parse.urlencode({'q': url, 'vt': 'facebook'}).encode('utf-8')
    api_url = "https://v3.fdownloader.net/api/ajaxSearch"
    req = urllib.request.Request(api_url, data=data, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '*/*',
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode('utf-8')
            print("SUCCESS:", body[:200])
    except Exception as e:
        if hasattr(e, 'read'):
            print("ERROR BODY:", e.read().decode()[:200])
        else:
            print("ERROR:", e)

if __name__ == '__main__':
    test_publer('https://www.facebook.com/watch/?v=10156054817757912')
    test_fdownloader('https://www.facebook.com/watch/?v=10156054817757912')
