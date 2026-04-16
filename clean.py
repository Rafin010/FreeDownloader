import io
import re

def clean_dashboard():
    fp = r'e:\_free downloader Projext\backend\templates\dashboard.html'
    with io.open(fp, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()

    text = re.sub(r'<option value="software">.*Software</option>', '<option value="software">Software</option>', text)
    text = re.sub(r'<option value="app">.*App</option>', '<option value="app">App</option>', text)
    text = re.sub(r'<option value="web">.*Web \(Website Link\)</option>', '<option value="web">Web (Website Link)</option>', text)

    text = re.sub(r'>(.*?) Icon / Image URL', '>Icon / Image URL', text)
    text = re.sub(r'>(.*?) Website / Download Link', '>Website / Download Link', text)
    text = re.sub(r'>(.*?) File Upload', '>File Upload', text)
    text = re.sub(r'>(.*?) Tips:', '>Tips:', text)

    with io.open(fp, 'w', encoding='utf-8') as f:
        f.write(text)

clean_dashboard()
print('Cleaned')
