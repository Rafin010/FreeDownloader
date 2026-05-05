from flask import Flask, render_template

app = Flask(__name__)

cards_data = [
    {
        "title": "Facebook Video Downloader",
        "url": "https://f.freedownloader.top",
        "img": "https://i.ibb.co.com/PstMVStg/Untitled-design.jpg",
        "hover_bg": "group-hover:bg-[#1877F2]",
        "shadow": "hover:shadow-[0_0_40px_rgba(24,119,242,0.5)] border-white/10 group-hover:border-[#1877F2]"
    },
    {
        "title": "Instagram Video Downloader",
        "url": "https://i.freedownloader.top",
        "img": "https://i.ibb.co.com/j9rhywh6/Untitled-design.png",
        "hover_bg": "group-hover:bg-gradient-to-tr group-hover:from-[#f09433] group-hover:via-[#dc2743] group-hover:to-[#bc1888]",
        "shadow": "hover:shadow-[0_0_40px_rgba(220,39,67,0.5)] border-white/10 group-hover:border-transparent"
    },
    {
        "title": "TikTok Video Downloader",
        "url": "https://t.freedownloader.top",
        "img": "https://i.ibb.co.com/gMCSyrx6/Untitled-design-2.jpg",
        "hover_bg": "group-hover:bg-[#010101]",
        "shadow": "hover:shadow-[0_0_40px_rgba(0,242,254,0.5)] border-white/10 group-hover:border-[#00f2fe]"
    },
    {
        "title": "YouTube Video Downloader",
        "url": "https://y.freedownloader.top",
        "img": "https://i.ibb.co.com/fVNmQKLs/Untitled-design-1.jpg",
        "hover_bg": "group-hover:bg-[#FF0000]",
        "shadow": "hover:shadow-[0_0_40px_rgba(255,0,0,0.5)] border-white/10 group-hover:border-[#FF0000]"
    },
    {
        "title": "Movie Video Downloader",
        "url": "https://movie.freedownloader.top",
        "img": "https://i.ibb.co.com/1GxTjF1J/Screenshot-2026-03-12-023922-removebg-preview.png",
        "hover_bg": "group-hover:bg-[#111827]",
        "shadow": "hover:shadow-[0_0_40px_rgba(99,102,241,0.5)] border-white/10 group-hover:border-[#6366f1]"
    },
    {
        "title": "Porn Video Downloader",
        "url": "https://p.freedownloader.top",
        "img": "https://i.ibb.co.com/1GxTjF1J/Screenshot-2026-03-12-023922-removebg-preview.png",
        "hover_bg": "group-hover:bg-[#000000]",
        "shadow": "hover:shadow-[0_0_40px_rgba(249,115,22,0.5)] border-white/10 group-hover:border-[#f97316]"
    }
]

@app.route('/')
def home():
    return render_template('index.html', cards=cards_data)

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)