import urllib.request
import json

def test_vyturex(url):
    print(f"\n--- Testing vyturex ---")
    req = urllib.request.Request(f"https://api.vyturex.com/ig?url={url}", headers={
        'User-Agent': 'Mozilla/5.0'
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print("SUCCESS:", resp.read().decode()[:200])
    except Exception as e:
        if hasattr(e, 'read'):
            print("ERROR BODY:", e.read().decode()[:200])
        else:
            print("ERROR:", e)

if __name__ == '__main__':
    test_vyturex('https://www.instagram.com/p/C_1Q3Y7B-Y_/')
