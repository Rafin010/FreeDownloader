import subprocess
from curl_cffi import requests
import re

def test_snapsave_ig(url):
    print(f"\n--- Testing Snapsave API for Instagram ---")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Origin': 'https://snapsave.app',
        'Referer': 'https://snapsave.app/',
    }
    data = {'url': url}
    try:
        response = requests.post("https://snapsave.app/action.php?catch=video", data=data, headers=headers, impersonate="chrome110")
        if response.status_code == 200:
            js_code = response.text
            js_code = js_code.replace('eval(', 'console.log(')
            with open('decode_snapsave.js', 'w', encoding='utf-8') as f:
                f.write(js_code)
            result = subprocess.run(['node', 'decode_snapsave.js'], capture_output=True, text=True)
            decoded_html = result.stdout
            print("Decoded snippet:", decoded_html[:500])
            links = re.findall(r'href=\\"(https?://[^\\"]+)\\"', decoded_html)
            if not links:
                links = re.findall(r'href="(https?://[^"]+)"', decoded_html)
            print("Found links:", len(links))
            for link in links:
                print("Link:", link[:100])
        else:
            print("Failed:", response.status_code)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_snapsave_ig("https://www.instagram.com/p/C_1Q3Y7B-Y_/")
