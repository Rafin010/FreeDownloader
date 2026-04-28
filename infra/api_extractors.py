"""
Multi-API Fallback Video Extractor — SnagSave-style approach.

Instead of relying solely on yt-dlp (which gets blocked by platforms),
this module uses multiple external API services as fallbacks:

1. Cobalt API instances (open-source, self-hostable)
2. Public scraper APIs (AllVideoDownloader-style endpoints)
3. Direct HTML scraping for Facebook/Instagram/TikTok
4. yt-dlp as final fallback

Usage:
    from infra.api_extractors import extract_video, download_video_via_api

    result = extract_video(url, platform='auto')
    # result = {'title': '...', 'thumbnail': '...', 'formats': [...], 'download_urls': {...}}
"""

import os
import re
import json
import time
import random
import logging
import hashlib
import urllib.request
import urllib.parse
import urllib.error
from html import unescape

logger = logging.getLogger(__name__)

# ── User-Agent Pool ───────────────────────────────────────────
_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/19.2 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 19_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/19.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
]


def _random_ua():
    return random.choice(_UA_POOL)


def _http_post_json(url, payload, headers=None, timeout=20):
    """Make a POST request with JSON body using urllib (no external deps)."""
    data = json.dumps(payload).encode('utf-8')
    hdrs = {
        'User-Agent': _random_ua(),
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, data=data, headers=hdrs, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8')), resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='ignore')
        try:
            return json.loads(body), e.code
        except Exception:
            return {'error': body[:500]}, e.code
    except Exception as e:
        return {'error': str(e)}, 0


def _http_get_json(url, headers=None, timeout=15):
    """Make a GET request returning JSON using urllib."""
    hdrs = {
        'User-Agent': _random_ua(),
        'Accept': 'application/json',
    }
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8')), resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='ignore')
        try:
            return json.loads(body), e.code
        except Exception:
            return {'error': body[:500]}, e.code
    except Exception as e:
        return {'error': str(e)}, 0


def _http_get_text(url, headers=None, timeout=15):
    """Make a GET request returning text using urllib."""
    hdrs = {
        'User-Agent': _random_ua(),
        'Accept': 'text/html,application/xhtml+xml,*/*',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='ignore'), resp.status
    except Exception as e:
        return str(e), 0


# ── Platform Detection ────────────────────────────────────────
def detect_platform(url):
    """Detect which platform a URL belongs to."""
    url_lower = url.lower()
    if any(d in url_lower for d in ['youtube.com', 'youtu.be']):
        return 'youtube'
    if any(d in url_lower for d in ['facebook.com', 'fb.watch', 'fb.com', 'fb.gg']):
        return 'facebook'
    if 'instagram.com' in url_lower:
        return 'instagram'
    if 'tiktok.com' in url_lower:
        return 'tiktok'
    if any(d in url_lower for d in ['twitter.com', 'x.com']):
        return 'twitter'
    return 'unknown'


# ══════════════════════════════════════════════════════════════
# Strategy 1: Cobalt API (open-source, best reliability)
# ══════════════════════════════════════════════════════════════

# Public cobalt instances — these rotate to avoid rate limits
COBALT_INSTANCES = [
    "https://api.cobalt.tools",
    "https://cobalt-api.kwiatekmiki.com",
    "https://cobalt.api.timelessnesses.me",
    "https://cobalt-api.ayo.tf",
    "https://co.eepy.today",
]


def _extract_via_cobalt(video_url, quality='1080'):
    """Extract video via Cobalt API instances."""
    payload = {
        'url': video_url,
        'videoQuality': quality,
        'audioFormat': 'mp3',
        'filenameStyle': 'basic',
    }

    for instance in COBALT_INSTANCES:
        try:
            api_url = f"{instance}/"
            logger.info("🔷 Trying Cobalt: %s", instance)

            data, status = _http_post_json(api_url, payload, headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            }, timeout=20)

            if status == 200 and data.get('status') in ('tunnel', 'redirect'):
                download_url = data.get('url', '')
                filename = data.get('filename', 'video.mp4')
                if download_url:
                    logger.info("✅ Cobalt succeeded via %s", instance)
                    return {
                        'source': f'cobalt:{instance}',
                        'download_url': download_url,
                        'filename': filename,
                        'title': filename.rsplit('.', 1)[0] if '.' in filename else filename,
                    }

            elif status == 200 and data.get('status') == 'picker':
                # Multiple items — return first video
                picker = data.get('picker', [])
                for item in picker:
                    if item.get('type') == 'video' and item.get('url'):
                        logger.info("✅ Cobalt picker succeeded via %s", instance)
                        return {
                            'source': f'cobalt:{instance}',
                            'download_url': item['url'],
                            'filename': 'video.mp4',
                            'title': 'Video',
                        }

            logger.warning("Cobalt %s returned: status=%s, data_status=%s",
                           instance, status, data.get('status'))

        except Exception as e:
            logger.warning("Cobalt %s failed: %s", instance, str(e)[:80])
            continue

    return None


# ══════════════════════════════════════════════════════════════
# Strategy 2: Direct Facebook HTML Scraping (mobile page)
# ══════════════════════════════════════════════════════════════

def _extract_fb_via_scraping(video_url):
    """Extract Facebook video by scraping mobile page HTML for video URLs."""
    try:
        # Convert to mobile URL for lighter page
        mobile_url = re.sub(r'https?://(?:www\.)?facebook\.com',
                            'https://m.facebook.com', video_url)

        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 19_0 like Mac OS X) '
                          'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/19.0 '
                          'Mobile/15E148 Safari/604.1',
            'Accept-Language': 'en-US,en;q=0.9',
            'Sec-Fetch-Mode': 'navigate',
        }

        html, status = _http_get_text(mobile_url, headers=headers, timeout=15)
        if status != 200 or len(html) < 100:
            return None

        # Extract HD and SD video URLs from page source
        download_urls = {}

        # Pattern 1: browser_native_hd_url / browser_native_sd_url
        hd_match = re.search(r'browser_native_hd_url\\":\\"([^"\\]+)', html)
        sd_match = re.search(r'browser_native_sd_url\\":\\"([^"\\]+)', html)

        # Pattern 2: playable_url_quality_hd / playable_url
        if not hd_match:
            hd_match = re.search(r'playable_url_quality_hd\\":\\"([^"\\]+)', html)
        if not sd_match:
            sd_match = re.search(r'playable_url\\":\\"([^"\\]+)', html)

        # Pattern 3: video_url encoded
        if not sd_match:
            sd_match = re.search(r'"video_url":"([^"]+)"', html)

        # Pattern 4: data-video-url
        if not sd_match:
            sd_match = re.search(r'data-video-url="([^"]+)"', html)

        # Pattern 5: og:video meta tag
        if not sd_match:
            sd_match = re.search(r'<meta\s+property="og:video"\s+content="([^"]+)"', html)
            if not sd_match:
                sd_match = re.search(r'<meta\s+property="og:video:url"\s+content="([^"]+)"', html)

        def _decode_fb_url(raw):
            """Decode Facebook's escaped video URLs."""
            decoded = raw.replace('\\/', '/').replace('\\u0025', '%')
            decoded = urllib.parse.unquote(decoded)
            # Remove unicode escapes
            decoded = decoded.encode().decode('unicode_escape', errors='ignore')
            return decoded

        if hd_match:
            download_urls['hd'] = _decode_fb_url(hd_match.group(1))
        if sd_match:
            download_urls['sd'] = _decode_fb_url(sd_match.group(1))

        # Extract title
        title = 'Facebook Video'
        title_match = re.search(r'<title>([^<]+)</title>', html)
        if title_match:
            title = unescape(title_match.group(1)).strip()
            if len(title) > 80:
                title = title[:77] + '...'

        # Extract thumbnail
        thumb = ''
        thumb_match = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', html)
        if thumb_match:
            thumb = unescape(thumb_match.group(1))

        if download_urls:
            logger.info("✅ FB scraping succeeded: %d quality options", len(download_urls))
            return {
                'source': 'fb_scraping',
                'title': title,
                'thumbnail': thumb,
                'download_urls': download_urls,
                'download_url': download_urls.get('hd') or download_urls.get('sd'),
            }

    except Exception as e:
        logger.warning("FB scraping failed: %s", str(e)[:100])

    return None


# ══════════════════════════════════════════════════════════════
# Strategy 3: Public Video Download API Services
# ══════════════════════════════════════════════════════════════

# These are free API endpoints that work like snapsave.app
SOCIAL_API_ENDPOINTS = [
    {
        'name': 'saveFrom-style',
        'url': 'https://cdn{n}.saveig.app/api/ajaxSearch',
        'method': 'POST',
        'form_data': True,
    },
]


def _extract_via_social_api(video_url, platform):
    """Try social media download APIs (snapsave/saveig-style)."""
    try:
        # Try saveig/snapsave style API
        for n in [76, 77, 78, 79, 80]:
            try:
                api_url = f"https://v3.saveig.app/api/ajaxSearch"
                form_data = urllib.parse.urlencode({
                    'q': video_url,
                    'lang': 'en',
                }).encode('utf-8')

                req = urllib.request.Request(api_url, data=form_data, headers={
                    'User-Agent': _random_ua(),
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': '*/*',
                    'Origin': 'https://saveig.app',
                    'Referer': 'https://saveig.app/',
                })

                with urllib.request.urlopen(req, timeout=15) as resp:
                    result = json.loads(resp.read().decode('utf-8'))

                if result.get('status') == 'ok' and result.get('data'):
                    html_data = result['data']
                    # Parse download links from returned HTML
                    links = re.findall(r'href="(https?://[^"]+)"', html_data)
                    video_links = [l for l in links if any(
                        ext in l.lower() for ext in ['.mp4', 'video', 'download']
                    )]
                    if video_links:
                        logger.info("✅ Social API succeeded")
                        return {
                            'source': 'social_api',
                            'download_url': video_links[0],
                            'title': 'Video',
                        }
            except Exception:
                continue

    except Exception as e:
        logger.warning("Social API failed: %s", str(e)[:100])

    return None


# ══════════════════════════════════════════════════════════════
# Strategy 4: TikTok Direct API
# ══════════════════════════════════════════════════════════════

def _extract_tiktok_direct(video_url):
    """Extract TikTok video via their oEmbed + web scraping."""
    try:
        # Try oEmbed first for metadata
        oembed_url = f"https://www.tiktok.com/oembed?url={urllib.parse.quote(video_url, safe='')}"
        data, status = _http_get_json(oembed_url, timeout=10)

        title = 'TikTok Video'
        thumb = ''
        if status == 200:
            title = data.get('title', 'TikTok Video')[:80]
            thumb = data.get('thumbnail_url', '')

        return {
            'source': 'tiktok_oembed',
            'title': title,
            'thumbnail': thumb,
            # TikTok oEmbed doesn't give download URL, but gives metadata
            # Cobalt or yt-dlp will handle the actual download
        }

    except Exception as e:
        logger.warning("TikTok direct failed: %s", str(e)[:80])
    return None


# ══════════════════════════════════════════════════════════════
# Strategy 5: Instagram oEmbed + Scraping
# ══════════════════════════════════════════════════════════════

def _extract_ig_direct(video_url):
    """Extract Instagram video metadata via oEmbed."""
    try:
        oembed_url = f"https://api.instagram.com/oembed?url={urllib.parse.quote(video_url, safe='')}"
        data, status = _http_get_json(oembed_url, timeout=10)

        if status == 200:
            return {
                'source': 'ig_oembed',
                'title': data.get('title', 'Instagram Video')[:80],
                'thumbnail': data.get('thumbnail_url', ''),
                'author': data.get('author_name', ''),
            }
    except Exception as e:
        logger.warning("IG oEmbed failed: %s", str(e)[:80])
    return None


# ══════════════════════════════════════════════════════════════
# Main Extraction Function — The SnagSave-style approach
# ══════════════════════════════════════════════════════════════

def extract_video(url, platform='auto', quality='1080'):
    """Extract video download info using multiple API fallback strategies.

    This is the core function that makes the downloader work like snapsave.app.
    It tries multiple strategies in order of reliability:

    1. Cobalt API (best — works for YouTube, FB, IG, TikTok, Twitter)
    2. Platform-specific scraping (Facebook HTML scraping)
    3. Social media download APIs
    4. Returns None so caller can fallback to yt-dlp

    Args:
        url: Video URL to extract
        platform: 'youtube', 'facebook', 'instagram', 'tiktok', or 'auto'
        quality: Video quality ('1080', '720', '480', etc.)

    Returns:
        dict with keys: source, download_url, title, thumbnail, etc.
        None if all strategies fail
    """
    if platform == 'auto':
        platform = detect_platform(url)

    logger.info("🚀 API extraction started for %s (%s)", url[:60], platform)

    # ── Strategy 1: Cobalt API (works for ALL platforms) ──────
    result = _extract_via_cobalt(url, quality)
    if result and result.get('download_url'):
        return result

    # ── Strategy 2: Platform-specific scraping ────────────────
    if platform == 'facebook':
        result = _extract_fb_via_scraping(url)
        if result and result.get('download_url'):
            return result

    # ── Strategy 3: Social media APIs ─────────────────────────
    result = _extract_via_social_api(url, platform)
    if result and result.get('download_url'):
        return result

    # ── Strategy 4: Platform-specific oEmbed (metadata only) ──
    if platform == 'tiktok':
        meta = _extract_tiktok_direct(url)
        if meta:
            # Return metadata even without download_url
            # The caller (yt-dlp) can use this for display
            return meta

    if platform == 'instagram':
        meta = _extract_ig_direct(url)
        if meta:
            return meta

    logger.warning("⚠️  All API extraction strategies failed for: %s", url[:60])
    return None


def download_video_stream(download_url, filepath, timeout=120):
    """Download a video from a direct URL to a file path.

    Used when an API strategy returns a direct download URL.

    Args:
        download_url: Direct video URL
        filepath: Local path to save the file
        timeout: Request timeout in seconds

    Returns:
        True if download succeeded, False otherwise
    """
    try:
        req = urllib.request.Request(download_url, headers={
            'User-Agent': _random_ua(),
            'Accept': '*/*',
        })

        with urllib.request.urlopen(req, timeout=timeout) as resp:
            with open(filepath, 'wb') as f:
                while True:
                    chunk = resp.read(65536)  # 64KB chunks
                    if not chunk:
                        break
                    f.write(chunk)

        file_size = os.path.getsize(filepath)
        if file_size > 10240:  # At least 10KB
            logger.info("✅ API download complete: %s (%d bytes)", filepath, file_size)
            return True
        else:
            logger.warning("Downloaded file too small (%d bytes), removing", file_size)
            os.remove(filepath)
            return False

    except Exception as e:
        logger.error("API download failed: %s", str(e)[:120])
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass
        return False
