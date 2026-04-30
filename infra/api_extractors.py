"""
Production Multi-API Fallback Video Extractor

CONFIRMED WORKING STRATEGIES (April 2026):
- TikTok:    tikwm.com API (POST) -> returns direct MP4 URLs
- Facebook:  yt-dlp + impersonate + cookies (primary) | Snapsave JS decode (fallback)
- Instagram: yt-dlp + impersonate + cookies (needs valid IG cookies)
- Porn:      yt-dlp + impersonate (works for all major adult sites)
- YouTube:   yt-dlp + impersonate (standard)
"""

import os
import re
import json
import time
import random
import logging
import urllib.request
import urllib.parse
import subprocess
import tempfile

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════
# Utility
# ══════════════════════════════════════════════════════════════
_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/19.2 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 19_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/19.0 Mobile/15E148 Safari/604.1",
]

def _random_ua():
    return random.choice(_UA_POOL)


def detect_platform(url):
    """Detect the platform from a URL."""
    url_lower = url.lower()
    if any(d in url_lower for d in ['youtube.com', 'youtu.be']):
        return 'youtube'
    if any(d in url_lower for d in ['facebook.com', 'fb.watch', 'fb.com', 'fb.gg', 'fb.reel']):
        return 'facebook'
    if 'instagram.com' in url_lower:
        return 'instagram'
    if 'tiktok.com' in url_lower:
        return 'tiktok'
    if any(d in url_lower for d in ['twitter.com', 'x.com']):
        return 'twitter'
    return 'unknown'


# ══════════════════════════════════════════════════════════════
# Strategy 1: TikTok via tikwm.com (CONFIRMED WORKING)
# ══════════════════════════════════════════════════════════════
def _extract_tiktok_via_tikwm(video_url):
    """
    tikwm.com API — POST with form data.
    Returns watermark-free MP4 download URLs.
    """
    logger.info("TikTok: Trying tikwm.com API for %s", video_url[:60])
    try:
        data = urllib.parse.urlencode({
            'url': video_url,
            'count': 12,
            'cursor': 0,
            'web': 1,
            'hd': 1
        }).encode()
        req = urllib.request.Request(
            'https://www.tikwm.com/api/',
            data=data,
            headers={
                'User-Agent': _random_ua(),
                'Origin': 'https://www.tikwm.com',
                'Referer': 'https://www.tikwm.com/',
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode('utf-8'))

        if result.get('code') == 0 and result.get('data'):
            item = result['data']
            # tikwm returns relative paths — prepend base URL
            base = 'https://www.tikwm.com'
            play = item.get('play', '')
            hdplay = item.get('hdplay', '')

            if play and not play.startswith('http'):
                play = base + play
            if hdplay and not hdplay.startswith('http'):
                hdplay = base + hdplay

            download_url = hdplay or play
            if download_url:
                logger.info("tikwm SUCCESS: %s", item.get('title', '')[:50])
                return {
                    'source': 'tikwm',
                    'title': item.get('title', 'TikTok Video'),
                    'thumbnail': item.get('cover', ''),
                    'download_url': download_url,
                    'download_urls': {'hd': hdplay, 'sd': play},
                }
        else:
            logger.warning("tikwm returned code=%s msg=%s",
                           result.get('code'), result.get('msg', ''))
    except Exception as e:
        logger.warning("tikwm failed: %s", str(e)[:100])
    return None


# ══════════════════════════════════════════════════════════════
# Strategy 2: Facebook via Snapsave (JS decode fallback)
# ══════════════════════════════════════════════════════════════
def _extract_fb_via_snapsave(video_url):
    """
    Snapsave.app — posts to action.php, returns obfuscated JS
    that must be decoded via Node.js to extract fbcdn download links.
    """
    try:
        from curl_cffi import requests as cffi_requests
    except ImportError:
        logger.warning("curl_cffi not available, skipping Snapsave")
        return None

    logger.info("Facebook: Trying snapsave.app for %s", video_url[:60])
    try:
        resp = cffi_requests.post(
            "https://snapsave.app/action.php?catch=video",
            data={'url': video_url},
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Origin': 'https://snapsave.app',
                'Referer': 'https://snapsave.app/',
            },
            impersonate='chrome110',
            timeout=15,
        )
        if resp.status_code != 200:
            return None

        text = resp.text
        if not ('eval(function' in text or text.startswith('var ')):
            # Might be direct HTML — try extracting links directly
            links = re.findall(r'href="(https?://[^"]+)"', text)
            video_links = [l for l in links if 'fbcdn' in l or 'rapidcdn' in l or 'mp4' in l]
            if video_links:
                return {
                    'source': 'snapsave',
                    'title': 'Facebook Video',
                    'thumbnail': '',
                    'download_url': video_links[0],
                }
            return None

        # Decode obfuscated JS via Node.js
        js_code = text.replace('eval(', 'console.log(')
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.js', delete=False, encoding='utf-8',
            dir=tempfile.gettempdir()
        ) as f:
            f.write(js_code)
            tmppath = f.name

        try:
            result = subprocess.run(
                ['node', tmppath],
                capture_output=True, text=True, timeout=10
            )
            html = result.stdout
        finally:
            if os.path.exists(tmppath):
                os.unlink(tmppath)

        if 'error_video_private' in html or 'private' in html.lower():
            logger.warning("Snapsave: video is private")
            return None

        # Extract all hrefs (escaped and unescaped)
        links = re.findall(r'href=\\"(https?://[^\\"]+)\\"', html)
        if not links:
            links = re.findall(r'href="(https?://[^"]+)"', html)

        video_links = []
        for l in links:
            clean = l.replace('\\/', '/').replace('\\u0026', '&')
            if 'fbcdn' in clean or 'rapidcdn' in clean or 'mp4' in clean or 'video' in clean:
                if clean not in video_links:
                    video_links.append(clean)

        if video_links:
            logger.info("Snapsave SUCCESS: %d links found", len(video_links))
            return {
                'source': 'snapsave',
                'title': 'Facebook Video',
                'thumbnail': '',
                'download_url': video_links[0],
                'download_urls': {
                    'hd': video_links[0],
                    'sd': video_links[-1] if len(video_links) > 1 else video_links[0],
                },
            }
    except Exception as e:
        logger.warning("Snapsave failed: %s", str(e)[:100])
    return None


# ══════════════════════════════════════════════════════════════
# Strategy 3: Facebook HTML scraping (legacy mobile fallback)
# ══════════════════════════════════════════════════════════════
def _extract_fb_via_scraping(video_url):
    """Scrape mobile Facebook page for video URLs in JSON."""
    logger.info("Facebook: Trying mobile scraping for %s", video_url[:60])
    try:
        mobile_url = re.sub(
            r'https?://(?:www\.)?facebook\.com',
            'https://m.facebook.com',
            video_url
        )
        req = urllib.request.Request(mobile_url, headers={
            'User-Agent': ('Mozilla/5.0 (iPhone; CPU iPhone OS 19_0 like Mac OS X) '
                           'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/19.0 '
                           'Mobile/15E148 Safari/604.1'),
            'Accept-Language': 'en-US,en;q=0.9',
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')

        hd = re.search(r'browser_native_hd_url\\":\\"([^"\\]+)', html)
        sd = re.search(r'browser_native_sd_url\\":\\"([^"\\]+)', html)
        if not hd:
            hd = re.search(r'playable_url_quality_hd\\":\\"([^"\\]+)', html)
        if not sd:
            sd = re.search(r'playable_url\\":\\"([^"\\]+)', html)
        if not sd:
            sd = re.search(r'"video_url":"([^"]+)"', html)

        def _decode(raw):
            decoded = raw.replace('\\/', '/').replace('\\u0025', '%')
            decoded = urllib.parse.unquote(decoded)
            return decoded.encode().decode('unicode_escape', errors='ignore')

        urls = {}
        if hd:
            urls['hd'] = _decode(hd.group(1))
        if sd:
            urls['sd'] = _decode(sd.group(1))

        if urls:
            logger.info("FB scraping SUCCESS: %s", list(urls.keys()))
            return {
                'source': 'fb_scraping',
                'title': 'Facebook Video',
                'thumbnail': '',
                'download_url': urls.get('hd') or urls.get('sd'),
                'download_urls': urls,
            }
    except Exception as e:
        logger.warning("FB scraping failed: %s", str(e)[:100])
    return None


# ══════════════════════════════════════════════════════════════
# Main Extraction Function
# ══════════════════════════════════════════════════════════════
def extract_video(url, platform='auto', quality='1080'):
    """
    Multi-strategy video extraction.

    Returns dict with keys:
        source, title, thumbnail, download_url, download_urls (optional)
    or None if all strategies fail.
    """
    if platform == 'auto':
        platform = detect_platform(url)

    logger.info("API extraction for %s (%s)", url[:60], platform)

    # ── TikTok: tikwm API ──
    if platform == 'tiktok':
        result = _extract_tiktok_via_tikwm(url)
        if result and result.get('download_url'):
            return result

    # ── Facebook: Snapsave -> mobile scraping ──
    if platform == 'facebook':
        result = _extract_fb_via_snapsave(url)
        if result and result.get('download_url'):
            return result

        result = _extract_fb_via_scraping(url)
        if result and result.get('download_url'):
            return result

    # ── Instagram / YouTube / Porn / Others ──
    # These rely on yt-dlp with impersonation in the service app.py files.
    # No reliable free external API exists for Instagram as of April 2026.

    logger.warning("All API strategies failed for: %s (%s)", url[:60], platform)
    return None


def download_video_stream(download_url, filepath, timeout=120):
    """Download a video from a direct URL to a local file."""
    try:
        req = urllib.request.Request(download_url, headers={
            'User-Agent': _random_ua(),
            'Accept': '*/*',
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            with open(filepath, 'wb') as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)

        if os.path.getsize(filepath) > 10240:
            logger.info("API download complete: %s (%d bytes)",
                        filepath, os.path.getsize(filepath))
            return True

        logger.warning("Downloaded file too small: %s", filepath)
        os.remove(filepath)
    except Exception as e:
        logger.error("API download failed: %s", str(e)[:120])
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass
    return False
