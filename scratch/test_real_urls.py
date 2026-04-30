# -*- coding: utf-8 -*-
"""Test with REAL public URLs found from TikTok and Facebook."""
import sys, os, re, json, urllib.request, urllib.parse, subprocess, tempfile
sys.stdout.reconfigure(encoding='utf-8')
from curl_cffi import requests

TIKTOK_URL = "https://www.tiktok.com/@mdsahlom490/video/7633026307168767252"
FB_URL = "https://www.facebook.com/watch/?v=26710336675272729"

def test_snaptik_tiktok():
    print("\n=== SNAPTIK.APP (TikTok) ===")
    try:
        r = requests.get('https://snaptik.app/en', impersonate='chrome110', timeout=10)
        token = re.search(r'name="token"\s+value="([^"]+)"', r.text)
        if not token:
            print("  No token found")
            return False
        print(f"  Token: {token.group(1)[:30]}...")
        
        data = {'url': TIKTOK_URL, 'token': token.group(1)}
        r2 = requests.post('https://snaptik.app/abc2?url=dl',
                          data=data,
                          headers={'Origin': 'https://snaptik.app', 'Referer': 'https://snaptik.app/en'},
                          impersonate='chrome110', timeout=15)
        print(f"  Post status: {r2.status_code}")
        
        # The response contains encoded HTML/JS
        text = r2.text
        if 'eval(' in text:
            js_code = text.replace('eval(', 'console.log(')
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8') as f:
                f.write(js_code)
                tmppath = f.name
            result = subprocess.run(['node', tmppath], capture_output=True, text=True, timeout=10)
            os.unlink(tmppath)
            decoded = result.stdout
            links = re.findall(r'href="(https?://[^"]+)"', decoded)
            dl_links = [l for l in links if '.mp4' in l or 'tiktokcdn' in l or 'snaptik' in l]
            print(f"  Download links: {len(dl_links)}")
            for l in dl_links[:3]:
                print(f"    {l[:120]}")
            return len(dl_links) > 0
        else:
            # Direct HTML response
            links = re.findall(r'href="(https?://[^"]+)"', text)
            dl_links = [l for l in links if '.mp4' in l or 'tiktokcdn' in l or 'snaptik' in l or 'download' in l]
            print(f"  Direct links: {len(dl_links)}")
            for l in dl_links[:3]:
                print(f"    {l[:120]}")
            if not dl_links:
                print(f"  Response preview: {text[:300]}")
            return len(dl_links) > 0
    except Exception as e:
        print(f"  Error: {e}")
    return False

def test_tikwm_post():
    print("\n=== TIKWM.COM POST (TikTok) ===")
    try:
        data = urllib.parse.urlencode({
            'url': TIKTOK_URL,
            'count': 12,
            'cursor': 0,
            'web': 1,
            'hd': 1
        }).encode()
        req = urllib.request.Request('https://www.tikwm.com/api/',
                                     data=data,
                                     headers={
                                         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                                         'Origin': 'https://www.tikwm.com',
                                         'Referer': 'https://www.tikwm.com/',
                                         'Content-Type': 'application/x-www-form-urlencoded'
                                     })
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
            print(f"  Code: {result.get('code')}")
            if result.get('code') == 0 and result.get('data'):
                d = result['data']
                print(f"  Title: {d.get('title','')[:60]}")
                print(f"  Play: {d.get('play','')[:80]}")
                print(f"  HD: {d.get('hdplay','N/A')[:80]}")
                return True
            else:
                print(f"  Msg: {result.get('msg')}")
    except Exception as e:
        print(f"  Error: {e}")
    return False

def test_snapsave_fb():
    print("\n=== SNAPSAVE (Facebook) ===")
    try:
        resp = requests.post("https://snapsave.app/action.php?catch=video",
                            data={'url': FB_URL},
                            headers={
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                                'Origin': 'https://snapsave.app',
                                'Referer': 'https://snapsave.app/',
                            },
                            impersonate='chrome110', timeout=15)
        print(f"  Status: {resp.status_code}")
        if resp.status_code == 200:
            text = resp.text
            if 'eval(function' in text or text.startswith('var '):
                js_code = text.replace('eval(', 'console.log(')
                with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8') as f:
                    f.write(js_code)
                    tmppath = f.name
                result = subprocess.run(['node', tmppath], capture_output=True, text=True, timeout=10)
                os.unlink(tmppath)
                html = result.stdout
                
                # Check for errors first
                if 'error' in html.lower() and 'private' in html.lower():
                    print("  Video is private/unavailable")
                    return False
                
                links = re.findall(r'href=\\"(https?://[^\\"]+)\\"', html)
                if not links:
                    links = re.findall(r'href="(https?://[^"]+)"', html)
                video_links = []
                for l in links:
                    clean = l.replace('\\/', '/').replace('\\u0026', '&')
                    if 'fbcdn' in clean or 'mp4' in clean or 'video' in clean:
                        video_links.append(clean)
                print(f"  Video links: {len(video_links)}")
                for l in video_links[:3]:
                    print(f"    {l[:120]}")
                if not video_links and links:
                    print(f"  All links: {len(links)}")
                    for l in links[:5]:
                        print(f"    {l[:120]}")
                return len(video_links) > 0
    except Exception as e:
        print(f"  Error: {e}")
    return False

def test_ytdlp_fb():
    print("\n=== YT-DLP + IMPERSONATE (Facebook) ===")
    try:
        result = subprocess.run(
            ['yt-dlp', '--impersonate', 'chrome', '--cookies', 'fb_downloader/cookies.txt',
             '--dump-json', '--no-download', FB_URL],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            print(f"  SUCCESS! Title: {data.get('title','')[:60]}")
            print(f"  Formats: {len(data.get('formats', []))}")
            return True
        else:
            print(f"  Error: {result.stderr[:200]}")
    except Exception as e:
        print(f"  Error: {e}")
    return False

if __name__ == '__main__':
    print("=" * 60)
    print("  TESTING WITH REAL PUBLIC URLs")
    print("=" * 60)
    print(f"  TikTok: {TIKTOK_URL}")
    print(f"  Facebook: {FB_URL}")
    
    results = {}
    results['tikwm_tiktok'] = test_tikwm_post()
    results['snaptik_tiktok'] = test_snaptik_tiktok()
    results['snapsave_fb'] = test_snapsave_fb()
    results['ytdlp_fb'] = test_ytdlp_fb()
    
    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)
    for k, v in results.items():
        s = "PASS" if v else "FAIL"
        print(f"  {k:25s} : {s}")
