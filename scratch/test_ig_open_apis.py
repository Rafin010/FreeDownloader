import urllib.request
import json

def test_api(name, url):
    print(f"\n--- Testing {name} ---")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read().decode('utf-8')
            print("SUCCESS:", data[:200])
    except Exception as e:
        print("ERROR:", e)

if __name__ == '__main__':
    ig_url = "https://www.instagram.com/p/C_1Q3Y7B-Y_/"
    test_api('aemt.me', f'https://aemt.me/download/igdl?url={ig_url}')
    test_api('tiklydown', f'https://api.tiklydown.eu.org/api/download?url={ig_url}')
    test_api('bk9.fun', f'https://bk9.fun/download/instagram?url={ig_url}')
