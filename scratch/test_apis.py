import requests

# Test TikTok
print("--- TikTok ---")
try:
    res = requests.post("http://75.127.1.75:8003/api/get_info", json={"url": "https://www.tiktok.com/@tiktok/video/7106594312292453675"})
    print(res.status_code)
    print(res.text)
except Exception as e:
    print(e)

# Test Instagram
print("--- Instagram ---")
try:
    res = requests.post("http://75.127.1.75:8002/api/get_info", json={"url": "https://www.instagram.com/p/C-U8G1eR3N2/"})
    print(res.status_code)
    print(res.text)
except Exception as e:
    print(e)
