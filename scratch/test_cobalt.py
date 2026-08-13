import sys
from curl_cffi import requests
url = "https://www.tiktok.com/@khaby.lame/video/7154284852655869190"

def test_cobalt():
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    data = {"url": url}
    try:
        r = requests.post("https://api.cobalt.tools/api/json", json=data, headers=headers, impersonate="chrome110")
        print("Cobalt:", r.status_code, r.text)
    except Exception as e:
        print("Cobalt err:", e)

test_cobalt()
