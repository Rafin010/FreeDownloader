import urllib.request
import urllib.parse
import json
import re

def test_tiktok(url):
    print(f"\n--- TikTok API: tikwm.com ---")
    api_url = f"https://www.tikwm.com/api/?url={urllib.parse.quote(url)}"
    req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if data.get('code') == 0:
                print("SUCCESS!")
                print(f"Title: {data['data'].get('title')}")
                print(f"Play URL: {data['data'].get('play')}")
            else:
                print("API returned error:", data)
    except Exception as e:
        print("Exception:", e)

def test_saveig(url):
    print(f"\n--- IG API: v3.saveig.app ---")
    api_url = "https://v3.saveig.app/api/ajaxSearch"
    data = urllib.parse.urlencode({'q': url, 'lang': 'en'}).encode('utf-8')
    req = urllib.request.Request(api_url, data=data, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '*/*',
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if data.get('status') == 'ok':
                print("SUCCESS!")
                print(f"Data length: {len(data.get('data', ''))}")
                links = re.findall(r'href="(https?://[^"]+)"', data['data'])
                print(f"Found links: {len(links)}")
                if links:
                    print(f"First link: {links[0]}")
            else:
                print("API returned error:", data)
    except Exception as e:
        print("Exception:", e)

def test_snapsave_fb(url):
    print(f"\n--- FB API: snapsave.app ---")
    api_url = "https://snapsave.app/action.php?catch=video"
    data = urllib.parse.urlencode({'url': url}).encode('utf-8')
    req = urllib.request.Request(api_url, data=data, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '*/*',
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode('utf-8')
            # Snapsave might return encoded JS or direct json?
            print("Response length:", len(body))
            if body.startswith('{'):
                print(json.loads(body))
            else:
                print("Body start:", body[:200])
    except Exception as e:
        print("Exception:", e)

if __name__ == '__main__':
    test_tiktok('https://www.tiktok.com/@tiktok/video/7106594312292453675')
    test_saveig('https://www.instagram.com/p/C_1Q3Y7B-Y_/')
    test_snapsave_fb('https://www.facebook.com/watch/?v=10156054817757912')
