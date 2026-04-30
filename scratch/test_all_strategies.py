"""
Comprehensive API tester - test ALL viable strategies at once
"""
from curl_cffi import requests as cffi_requests
import urllib.request
import json
import re
import subprocess
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

TEST_URLS = {
    'tiktok': 'https://www.tiktok.com/@khaby.lame/video/7004270927972852998',
    'facebook': 'https://www.facebook.com/reel/1234567890',
    'instagram': 'https://www.instagram.com/reel/DE-b6I-SjKk/',
}

def test_tikwm():
    """TikTok via tikwm.com"""
    print("\n" + "="*60)
    print("1. TIKWM (TikTok)")
    print("="*60)
    url = TEST_URLS['tiktok']
    api = f"https://www.tikwm.com/api/?url={url}"
    req = urllib.request.Request(api, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            if data.get('code') == 0 and data.get('data'):
                item = data['data']
                print(f"  ✅ SUCCESS!")
                print(f"  Title: {item.get('title','')[:60]}")
                print(f"  Play URL: {item.get('play','')[:80]}")
                print(f"  HD Play: {item.get('hdplay','')[:80]}")
                print(f"  Cover: {item.get('cover','')[:80]}")
                return True
            else:
                print(f"  ❌ Bad response: code={data.get('code')}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    return False

def test_cobalt_v11():
    """Cobalt API v11 (api.cobalt.tools)"""
    print("\n" + "="*60)
    print("2. COBALT v11 (api.cobalt.tools)")
    print("="*60)
    
    # First check the API info
    try:
        r = cffi_requests.get("https://api.cobalt.tools/", impersonate="chrome110", timeout=10)
        info = r.json()
        print(f"  API Version: {info.get('cobalt', {}).get('version', 'unknown')}")
    except Exception as e:
        print(f"  ❌ Cannot reach API: {e}")
        return False
    
    # Test with TikTok
    for platform, url in TEST_URLS.items():
        print(f"\n  Testing {platform}...")
        try:
            payload = {
                'url': url,
                'videoQuality': '1080',
                'filenameStyle': 'basic',
            }
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            }
            r = cffi_requests.post("https://api.cobalt.tools/", 
                                   json=payload, headers=headers,
                                   impersonate="chrome110", timeout=15)
            print(f"    Status: {r.status_code}")
            data = r.json()
            print(f"    Response: {json.dumps(data)[:200]}")
            if data.get('url') or data.get('picker'):
                print(f"    ✅ SUCCESS!")
            elif data.get('status') == 'error':
                print(f"    ❌ Error: {data.get('error', {}).get('code', 'unknown')}")
        except Exception as e:
            print(f"    ❌ Error: {e}")

def test_snapsave_fb():
    """Snapsave for Facebook"""
    print("\n" + "="*60)
    print("3. SNAPSAVE (Facebook)")
    print("="*60)
    url = "https://www.facebook.com/watch/?v=345678901234567"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Origin': 'https://snapsave.app',
        'Referer': 'https://snapsave.app/',
    }
    try:
        resp = cffi_requests.post("https://snapsave.app/action.php?catch=video", 
                                   data={'url': url}, headers=headers,
                                   impersonate="chrome110", timeout=15)
        print(f"  Status: {resp.status_code}")
        if resp.status_code == 200:
            text = resp.text
            if 'eval(function' in text or text.startswith('var '):
                print(f"  ✅ Got JS payload ({len(text)} bytes) — decoding needed")
                return True
            elif 'error' in text.lower():
                print(f"  ⚠️  Error in response: {text[:150]}")
            else:
                print(f"  Response: {text[:150]}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    return False

def test_yt_dlp_version():
    """Check yt-dlp version"""
    print("\n" + "="*60)
    print("4. YT-DLP VERSION CHECK")
    print("="*60)
    try:
        result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True, timeout=5)
        version = result.stdout.strip()
        print(f"  Current version: {version}")
        
        # Check if update is available
        result2 = subprocess.run(['yt-dlp', '-U', '--no-update'], capture_output=True, text=True, timeout=10)
        print(f"  Update check: {result2.stdout.strip()[:100]}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

def test_yt_dlp_tiktok():
    """Test yt-dlp directly on TikTok"""
    print("\n" + "="*60)
    print("5. YT-DLP DIRECT (TikTok)")
    print("="*60)
    url = TEST_URLS['tiktok']
    try:
        result = subprocess.run(
            ['yt-dlp', '--dump-json', '--no-download', url],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            print(f"  ✅ SUCCESS! Title: {data.get('title','')[:60]}")
            print(f"  Formats: {len(data.get('formats', []))}")
        else:
            print(f"  ❌ Failed: {result.stderr[:150]}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

def test_yt_dlp_porn():
    """Test yt-dlp on a porn site"""
    print("\n" + "="*60)
    print("6. YT-DLP (xVideos - adult)")
    print("="*60)
    url = "https://www.xvideos.com/video.iuybgfah177/test"
    try:
        result = subprocess.run(
            ['yt-dlp', '--dump-json', '--no-download', url],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            print(f"  ✅ SUCCESS! Title: {data.get('title','')[:60]}")
        else:
            err = result.stderr[:200]
            print(f"  ❌ Failed: {err}")
            if '404' in err or 'Not Found' in err:
                print("  Note: Test URL is fake, but 404 means yt-dlp CAN reach the site")
    except Exception as e:
        print(f"  ❌ Error: {e}")

if __name__ == '__main__':
    print("╔══════════════════════════════════════════════╗")
    print("║  COMPREHENSIVE API STATUS CHECK             ║")
    print("╚══════════════════════════════════════════════╝")
    
    test_yt_dlp_version()
    test_tikwm()
    test_cobalt_v11()
    test_snapsave_fb()
    test_yt_dlp_tiktok()
    test_yt_dlp_porn()
    
    print("\n\n" + "="*60)
    print("SUMMARY")
    print("="*60)
