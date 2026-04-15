from flask import Flask, render_template

app = Flask(__name__)

# প্রজেক্ট ডেটা
projects = [
    {
        "id": 1,
        "title": "SportyXi Lite",
        "category": "app",
        "developer": "Ifat Ahmed Rafin",
        "description": "লাইভ স্পোর্টস স্ট্রিমিং এবং রিয়েল-টাইম স্কোর আপডেটের জন্য একটি প্রফেশনাল প্ল্যাটফর্ম।",
        "version": "1.2.0",
        "rating": "4.8",
        "price": "Free",
        "download_link": "#download_app"
    },
    {
        "id": 2,
        "title": "Free Downloader",
        "category": "software",
        "developer": "Ifat Ahmed Rafin",
        "description": "যেকোনো প্ল্যাটফর্ম থেকে এক ক্লিকে হাই-কোয়ালিটি ভিডিও ডাউনলোড করার ফাস্ট এবং সিকিউর সফটওয়্যার।",
        "version": "2.0.1",
        "rating": "4.5",
        "price": "Free",
        "download_link": "#download_software"
    },
    {
        "id": 3,
        "title": "Neon Dashboard",
        "category": "web", # এটি 'web' ক্যাটাগরি, তাই ক্লিক করলে সরাসরি লিংকে যাবে
        "developer": "Ifat Ahmed Rafin",
        "description": "অ্যাডমিন প্যানেলের জন্য মডার্ন গ্লাসমরফিজম এবং ডার্ক থিম ড্যাশবোর্ড টেমপ্লেট।",
        "version": "1.0.0",
        "rating": "5.0",
        "price": "Free",
        "download_link": "https://www.google.com" # ডেমো ওয়েবসাইট লিংক
    }
]

@app.route('/')
def home():
    return render_template('index.html', projects=projects)

if __name__ == '__main__':
    app.run(debug=True)