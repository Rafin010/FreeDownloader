from curl_cffi import requests

def test_igram(url):
    print("\n--- Testing igram.world ---")
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Origin': 'https://igram.world',
        'Referer': 'https://igram.world/',
    }
    try:
        response = requests.post("https://igram.world/api/ajaxSearch", data={'q': url, 't': 'media', 'lang': 'en'}, headers=headers, impersonate="chrome110", timeout=10)
        if response.status_code == 200:
            print("SUCCESS:", response.text[:200])
        else:
            print("Failed:", response.text[:200])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_igram("https://www.instagram.com/p/C_1Q3Y7B-Y_/")
