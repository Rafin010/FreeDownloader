from curl_cffi import requests

def test_ip():
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Host': 'v3.saveig.app',
        'Origin': 'https://saveig.app',
        'Referer': 'https://saveig.app/',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {'q': 'https://www.instagram.com/p/C_1Q3Y7B-Y_/', 'lang': 'en'}
    
    try:
        # Use HTTPS to the Cloudflare IP
        r = requests.post("https://104.21.60.23/api/ajaxSearch", data=data, headers=headers, impersonate="chrome110", verify=False, timeout=10)
        print("Status:", r.status_code)
        print("Response:", r.text[:200])
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    test_ip()
