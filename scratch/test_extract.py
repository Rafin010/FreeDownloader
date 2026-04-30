import sys
import os

# Add the project root to sys.path
sys.path.insert(0, r"e:\_free downloader Projext")

from infra.api_extractors import extract_video

test_urls = {
    'facebook': 'https://www.facebook.com/watch/?v=10156054817757912',
    'tiktok': 'https://www.tiktok.com/@tiktok/video/7106594312292453675',
    'instagram': 'https://www.instagram.com/p/C_1Q3Y7B-Y_/',
    'porn': 'https://www.pornhub.com/view_video.php?viewkey=ph5e0f9b06d4e8c'
}

for platform, url in test_urls.items():
    print(f"\n--- Testing {platform} ---")
    try:
        res = extract_video(url, platform=platform)
        if res:
            print(f"SUCCESS: {res.get('source')}")
            print(f"Title: {res.get('title')}")
            print(f"Download URL: {res.get('download_url')}")
        else:
            print("FAILED: All API extractors returned None")
    except Exception as e:
        print(f"ERROR: {e}")
