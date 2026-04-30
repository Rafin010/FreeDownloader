import urllib.request
import json

def test_api():
    url = "https://www.instagram.com/p/C_1Q3Y7B-Y_/"
    print("\n--- Testing ryzendesu ---")
    try:
        req = urllib.request.Request(f"https://api.ryzendesu.vip/api/downloader/igdl?url={url}", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            print("SUCCESS:", resp.read().decode()[:500])
    except Exception as e:
        print("ERROR:", e)

if __name__ == '__main__':
    test_api()
