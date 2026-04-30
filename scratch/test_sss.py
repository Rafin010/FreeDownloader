import urllib.request
import json
from curl_cffi import requests

def test_api(url, endpoint, origin):
    print(f"\n--- Testing {endpoint} ---")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Origin': origin,
        'Referer': f"{origin}/",
    }
    data = {'id': url, 'locale': 'en'} # sssinstagram format
    try:
        response = requests.post(endpoint, data=data, headers=headers, impersonate="chrome110", timeout=10)
        print("Status Code:", response.status_code)
        if response.status_code == 200:
            print("Response:", response.text[:200])
        else:
            print("Failed:", response.text[:100])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_api("https://www.instagram.com/p/C_1Q3Y7B-Y_/", "https://sssinstagram.com/request", "https://sssinstagram.com")
