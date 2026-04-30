import json
from curl_cffi import requests

def test_snapsave(url):
    print(f"\n--- Testing Snapsave API via curl-cffi ---")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Origin': 'https://snapsave.app',
        'Referer': 'https://snapsave.app/',
    }
    data = {'url': url}
    try:
        response = requests.post("https://snapsave.app/action.php?catch=video", data=data, headers=headers, impersonate="chrome110")
        print("Status Code:", response.status_code)
        if response.status_code == 200:
            print("Response:", response.text[:500])
        else:
            print("Failed:", response.text[:200])
    except Exception as e:
        print("Error:", e)

def test_snapinsta(url):
    print(f"\n--- Testing Snapinsta API via curl-cffi ---")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Origin': 'https://snapinsta.app',
        'Referer': 'https://snapinsta.app/',
    }
    data = {'url': url, 'action': 'post'}
    try:
        response = requests.post("https://snapinsta.app/action.php", data=data, headers=headers, impersonate="chrome110")
        print("Status Code:", response.status_code)
        if response.status_code == 200:
            print("Response:", response.text[:500])
        else:
            print("Failed:", response.text[:200])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_snapsave("https://www.facebook.com/watch/?v=10156054817757912")
    test_snapinsta("https://www.instagram.com/p/C_1Q3Y7B-Y_/")
