const faqData = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "How to Download Facebook Videos Online?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "You can download Facebook videos easily. Just copy the video link from Facebook, paste it into our Facebook Video Downloader tool, select your preferred quality (like 1080p HD or 4K), and hit download."
      }
    },
    {
      "@type": "Question",
      "name": "Can I Download Facebook Reels in HD?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes! Our tool acts as a perfect Facebook Reels Downloader. Paste the Reel link, and you can save it directly to your phone's gallery in HD quality."
      }
    },
    {
      "@type": "Question",
      "name": "Why Facebook Videos Cannot Be Downloaded sometimes?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Sometimes Facebook videos cannot be downloaded if the video is set to private, the link is broken, or the video has been deleted by the owner. Ensure the video is public."
      }
    },
    {
      "@type": "Question",
      "name": "What is the Best Facebook Video Downloader?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Free Downloader is considered one of the best Facebook video downloader tools because it is 100% free, requires no app installation, and supports HD, 1080p, and 4K video downloads without any watermarks."
      }
    }
  ]
};

// ডাটাগুলোকে ওয়েবসাইটে ইনজেক্ট করার কোড
const script = document.createElement('script');
script.type = "application/ld+json";
script.text = JSON.stringify(faqData);
document.head.appendChild(script);