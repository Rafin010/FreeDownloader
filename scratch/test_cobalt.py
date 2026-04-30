import urllib.request
import urllib.parse
import json

def test_cobalt():
    url = "https://www.facebook.com/watch/?v=10156054817757912"
    payload = {
        'url': url,
    }
    api_url = "https://api.cobalt.tools/"
    req = urllib.request.Request(api_url, data=json.dumps(payload).encode('utf-8'), headers={
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Origin': 'https://cobalt.tools',
        'Referer': 'https://cobalt.tools/'
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print("SUCCESS:", resp.read().decode())
    except Exception as e:
        if hasattr(e, 'read'):
            print("ERROR BODY:", e.read().decode())
        else:
            print("ERROR:", e)

test_cobalt()
