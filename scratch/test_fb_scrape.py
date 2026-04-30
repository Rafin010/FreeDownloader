import sys
sys.path.insert(0, r"e:\_free downloader Projext")
from infra.api_extractors import _extract_fb_via_scraping

url = 'https://www.facebook.com/watch/?v=10156054817757912'
res = _extract_fb_via_scraping(url)
print(res)
