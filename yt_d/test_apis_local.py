import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from yt_d.app import app

client = app.test_client()

def run_tests():
    print("Testing /api/ads/config...")
    res = client.get('/api/ads/config')
    print("Status:", res.status_code)
    print("Data:", res.json)
    print("-" * 40)

    print("Testing /api/trending...")
    res = client.get('/api/trending')
    print("Status:", res.status_code)
    if res.status_code == 200:
        data = res.json.get("results", [])
        print(f"Got {len(data)} trending videos. First: {data[0] if data else None}")
    else:
        print("Error:", res.json)
    print("-" * 40)

    print("Testing /api/search?q=cyberpunk...")
    res = client.get('/api/search?q=cyberpunk')
    print("Status:", res.status_code)
    if res.status_code == 200:
        data = res.json.get("results", [])
        print(f"Got {len(data)} search results. First: {data[0] if data else None}")
    else:
        print("Error:", res.json)
    print("-" * 40)

    # Let's get the ID of the first search result to test the detail endpoint
    if res.status_code == 200 and res.json.get("results"):
        video_id = res.json["results"][0]["id"]
        print(f"Testing /api/video/{video_id}...")
        res = client.get(f'/api/video/{video_id}')
        print("Status:", res.status_code)
        if res.status_code == 200:
            data = res.json
            print("Title:", data.get('title'))
            print("Stream URL (len):", len(data.get('stream_url', '')) if data.get('stream_url') else "None")
            print("Formats:", data.get('download_formats'))
        else:
            print("Error:", res.json)
        print("-" * 40)

if __name__ == "__main__":
    run_tests()
