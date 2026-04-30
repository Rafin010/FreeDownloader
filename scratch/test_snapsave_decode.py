import subprocess
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
        if response.status_code == 200:
            js_code = response.text
            # Replace eval with console.log to output the decoded string instead of executing it
            if js_code.startswith('var '):
                # Usually: var _0xc... eval(function(...) ... )
                # We can replace 'eval(' with 'console.log('
                # Need to be careful to only replace the LAST eval if there are multiple, or just find eval(function
                js_code = js_code.replace('eval(', 'console.log(')
                
                # Execute in Node
                with open('decode_snapsave.js', 'w', encoding='utf-8') as f:
                    f.write(js_code)
                
                result = subprocess.run(['node', 'decode_snapsave.js'], capture_output=True, text=True)
                print("Decoded output:")
                decoded_html = result.stdout
                print(decoded_html[:1000])
                
                # Parse decoded HTML to find download links
                import re
                links = re.findall(r'href=\\"(https?://[^\\"]+)\\"', decoded_html)
                if not links:
                    links = re.findall(r'href="(https?://[^"]+)"', decoded_html)
                print(f"Found {len(links)} links")
                for link in links:
                    if 'mp4' in link or 'video' in link:
                        print("Download Link:", link[:100], "...")
        else:
            print("Failed:", response.text[:200])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_snapsave("https://www.facebook.com/watch/?v=10156054817757912")
