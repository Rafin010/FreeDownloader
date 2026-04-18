import os
import re

directories = ['freeStore', 'fb_downloader', 'yt_d', 'tik_d', 'insta_d', 'p_d']
base_dir = r"e:\_free downloader Projext"

def comment_out(content):
    # 1. Popunder scripts
    pattern_single_script = r'(<script src="https://pl[^>]*profitablecpmratenetwork\.com.*?"></script>)'
    
    def repl_html(m):
        code = m.group(1)
        if '<!-- AD SCRIPT DISABLED' in code:
            return code
        return f"<!-- AD SCRIPT DISABLED\n{code}\n-->"
        
    content = re.sub(pattern_single_script, repl_html, content)
    
    # 2. Divs containing highperformanceformat.com
    pattern_div = r'(<div[^>]*>[\s]*<script>[\s]*atOptions.*?invoke\.js"></script>[\s]*</div>)'
    content = re.sub(pattern_div, repl_html, content, flags=re.DOTALL)
    
    # 3. JS Direct Link logic
    # Matches:
    # // 1. Open Direct Link Ad in new tab
    # if (window.AD_CONFIG && window.AD_CONFIG.DIRECT_LINK_URL.includes("http")) {
    #     window.open(window.AD_CONFIG.DIRECT_LINK_URL, '_blank');
    # }
    pattern_direct_link = r'(// 1\. Open Direct Link Ad in new tab.*?window\.open\(window\.AD_CONFIG\.DIRECT_LINK_URL, \'_blank\'\);\n[\s]*})'
    
    def repl_js(m):
        code = m.group(1)
        if '// AD SCRIPT DISABLED' in code:
            return code
        commented = "\n".join([f"// AD SCRIPT DISABLED {line}" for line in code.split("\n")])
        return commented

    content = re.sub(pattern_direct_link, repl_js, content, flags=re.DOTALL)
    
    # 4. JS Pop-under logic
    pattern_pop_under = r'(// --- POP-UNDER / ON-CLICK AD LOGIC ---.*?document\.addEventListener\(\'paste\', triggerPopUnder, \{ capture: true \}\);)'
    content = re.sub(pattern_pop_under, repl_js, content, flags=re.DOTALL)
    
    return content

for d in directories:
    file_path = os.path.join(base_dir, d, 'templates', 'index.html')
    if not os.path.exists(file_path):
        continue
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = comment_out(content)
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Commented ads in {file_path}")
    else:
        print(f"No Ad changes needed in {file_path}")
