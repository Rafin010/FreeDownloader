import os
import glob

def add_meta_tags():
    project_dir = r"e:\_free downloader Projext"
    
    meta_tags = """
    <meta name="google-adsense-account" content="ca-pub-8275641937649551">
    <meta name="monetag" content="8eecf201ca29a630232ba4e117b33e26">
"""

    # Identify all HTML files in the project's templates directories
    html_files = glob.glob(os.path.join(project_dir, '*', 'templates', '*.html'))
    
    updated_files = 0
    for file_path in html_files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # If they are already in the file, skip
        if "8eecf201ca29a630232ba4e117b33e26" in content and "ca-pub-8275641937649551" in content:
            continue

        # Find the <head> tag or a suitable place near the top and insert the tags
        if "<head>" in content:
            content = content.replace("<head>", "<head>" + meta_tags, 1)
        elif '<meta charset="UTF-8">' in content:
            content = content.replace('<meta charset="UTF-8">', '<meta charset="UTF-8">' + meta_tags, 1)
        else:
            continue

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"Updated {file_path}")
        updated_files += 1

    print(f"Total files updated: {updated_files}")

if __name__ == "__main__":
    add_meta_tags()
