import requests

# Test TikTok Download
print("--- TikTok Download ---")
try:
    res = requests.get("http://75.127.1.75:8003/api/download?url=https://www.tiktok.com/@tiktok/video/7106594312292453675&res=720", stream=True)
    print(res.status_code)
    print(len(res.content))
except Exception as e:
    print(e)
