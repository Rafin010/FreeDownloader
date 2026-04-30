import urllib.request
import json

def test_publer(url):
    print(f"\n--- Testing Publer API ---")
    payload = {'url': url}
    api_url = "https://app.publer.io/api/v1/tools/media/extract"
    req = urllib.request.Request(api_url, data=json.dumps(payload).encode('utf-8'), headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print("SUCCESS:", resp.read().decode()[:500])
    except Exception as e:
        if hasattr(e, 'read'):
            print("ERROR BODY:", e.read().decode()[:500])
        else:
            print("ERROR:", e)

if __name__ == '__main__':
    test_publer('https://www.instagram.com/p/C_1Q3Y7B-Y_/')
