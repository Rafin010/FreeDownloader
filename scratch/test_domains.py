from curl_cffi import requests

domains = [
    "https://saveig.app/api/ajaxSearch",
    "https://v3.saveig.app/api/ajaxSearch",
    "https://fastdl.app/api/ajaxSearch",
    "https://snapinsta.app/action.php",
    "https://snapinsta.to/action.php",
    "https://snapinsta.io/action.php",
    "https://sssinstagram.com/request",
    "https://api.vyturex.com/ig?url=https://www.instagram.com/p/C_1Q3Y7B-Y_/",
    "https://co.wuk.sh/api/json",
    "https://api.cobalt.tools/",
    "https://cobalt.qewertyy.dev/api/json"
]

def test_all():
    print("Testing domains...")
    for d in domains:
        print(f"\n--- {d} ---")
        try:
            r = requests.get(d, impersonate="chrome110", timeout=5)
            print("Status:", r.status_code)
            print("Response:", r.text[:100])
        except Exception as e:
            print("Error:", str(e)[:100])

if __name__ == '__main__':
    test_all()
