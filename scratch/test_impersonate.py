import yt_dlp
opts = {'impersonate': yt_dlp.networking.impersonate.ImpersonateTarget(client='chrome')}
# Check if it works
try:
    with yt_dlp.YoutubeDL({'impersonate': yt_dlp.networking.impersonate.ImpersonateTarget(client='chrome')}) as ydl:
        print("Works with ImpersonateTarget object")
except Exception as e:
    print(f"Failed with ImpersonateTarget: {e}")

try:
    with yt_dlp.YoutubeDL({'impersonate': yt_dlp.networking.impersonate.ImpersonateTarget.from_str('chrome')}) as ydl:
        print("Works with ImpersonateTarget.from_str")
except Exception as e:
    print(f"Failed with ImpersonateTarget.from_str: {e}")
