import os

def update_delay():
    # Update delay in fb_downloader/app.py
    with open('e:\\_free downloader Projext\\fb_downloader\\app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = content.replace("FILE_EXPIRY_TIME = 600", "FILE_EXPIRY_TIME = 1800")
    content = content.replace("delete_file_delayed(filepath, delay=300)", "delete_file_delayed(filepath, delay=1800)")
    
    with open('e:\\_free downloader Projext\\fb_downloader\\app.py', 'w', encoding='utf-8') as f:
        f.write(content)

    # Update delay in yt_d/app.py
    with open('e:\\_free downloader Projext\\yt_d\\app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace("FILE_EXPIRY_TIME = 300", "FILE_EXPIRY_TIME = 1800")
    content = content.replace("delete_file_delayed(filepath, delay=300)", "delete_file_delayed(filepath, delay=1800)")
    with open('e:\\_free downloader Projext\\yt_d\\app.py', 'w', encoding='utf-8') as f:
        f.write(content)

update_delay()
