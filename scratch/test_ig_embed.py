import urllib.request
import re

def test_ig_embed(url):
    print("\n--- Testing IG Embed ---")
    embed_url = url.split('?')[0]
    if not embed_url.endswith('/'):
        embed_url += '/'
    embed_url += 'embed/captioned/'
    
    req = urllib.request.Request(embed_url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8')
            
            # Look for video URL
            video_match = re.search(r'video_url":"([^"]+)"', html)
            if video_match:
                video_url = video_match.group(1).replace('\\u0026', '&')
                print("FOUND VIDEO:", video_url[:150])
            else:
                print("No video found in embed")
    except Exception as e:
        print("ERROR:", e)

if __name__ == '__main__':
    test_ig_embed("https://www.instagram.com/p/C_1Q3Y7B-Y_/")
