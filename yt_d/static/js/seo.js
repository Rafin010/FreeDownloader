// ============================================
// YouTube Downloader - SEO Schema Injection
// Dynamically injects FAQPage JSON-LD schema
// ============================================

const faqData = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "How to Download YouTube Videos Online?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "You can download YouTube videos easily. Just copy the video link from YouTube, paste it into our YouTube Video Downloader tool, select your preferred quality (like 1080p HD or 4K), and hit download."
      }
    },
    {
      "@type": "Question",
      "name": "Can I Download YouTube Shorts in HD?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes! Our tool works perfectly as a YouTube Shorts Downloader. Paste the Shorts link, and you can save it directly to your device in HD quality without any watermark."
      }
    },
    {
      "@type": "Question",
      "name": "Why YouTube Videos Cannot Be Downloaded Sometimes?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Sometimes YouTube videos cannot be downloaded if the video is age-restricted, set to private, the link is broken, or the video has been removed by the creator. Ensure the video is public and the URL is correct."
      }
    },
    {
      "@type": "Question",
      "name": "What is the Best YouTube Video Downloader?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Free Downloader is considered one of the best YouTube video downloader tools because it is 100% free, requires no app installation, and supports HD, 1080p, 4K, and Shorts video downloads without any watermarks."
      }
    }
  ]
};

// Inject the structured data into the page head
const script = document.createElement('script');
script.type = "application/ld+json";
script.text = JSON.stringify(faqData);
document.head.appendChild(script);
