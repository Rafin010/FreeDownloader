import urllib.request
import urllib.parse
import json

def test_wuk_sh(url):
    print(f"\n--- Testing co.wuk.sh ---")
    payload = {'url': url, 'vQuality': '1080', 'isAudioOnly': False}
    req = urllib.request.Request("https://co.wuk.sh/api/json", data=json.dumps(payload).encode('utf-8'), headers={
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print("SUCCESS:", resp.read().decode())
    except Exception as e:
        if hasattr(e, 'read'):
            print("ERROR BODY:", e.read().decode())
        else:
            print("ERROR:", e)

if __name__ == '__main__':
    test_wuk_sh('https://www.instagram.com/p/C_1Q3Y7B-Y_/')
