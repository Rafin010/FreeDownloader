import urllib.request

def test_api(name, url):
    print(f"\n--- Testing {name} ---")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read().decode('utf-8')
            print("SUCCESS:", data[:300])
    except Exception as e:
        print("ERROR:", e)

if __name__ == '__main__':
    url = "https://www.instagram.com/p/C_1Q3Y7B-Y_/"
    test_api('akuari', f'https://api.akuari.my.id/downloader/igdl?link={url}')
    test_api('botcahx', f'https://api.botcahx.live/api/dowloader/igdowloader?url={url}')
    test_api('kwwv', f'https://api.kwwv.workers.dev/ig?url={url}')
