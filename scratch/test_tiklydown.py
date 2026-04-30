import urllib.request
import json
import ssl

def test_api(name, url):
    print(f"\n--- Testing {name} ---")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = resp.read().decode('utf-8')
            print("SUCCESS:", data[:500])
    except Exception as e:
        print("ERROR:", e)

if __name__ == '__main__':
    ig_url = "https://www.instagram.com/p/C_1Q3Y7B-Y_/"
    test_api('tiklydown', f'https://api.tiklydown.eu.org/api/download?url={ig_url}')
