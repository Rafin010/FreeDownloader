// ============================================
// Instagram Downloader - SEO Schema Injection
// Dynamically injects FAQPage JSON-LD schema
// ============================================

const faqData = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "How to Download Instagram Videos Online?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "You can download Instagram videos easily. Just copy the video or Reel link from Instagram, paste it into our Instagram Video Downloader tool, select your preferred quality, and hit download."
      }
    },
    {
      "@type": "Question",
      "name": "Can I Download Instagram Reels and Stories?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes! Our tool acts as a perfect Instagram Reels and Story Downloader. Paste the link, and you can save it directly to your phone's gallery in HD quality."
      }
    },
    {
      "@type": "Question",
      "name": "Why Instagram Videos Cannot Be Downloaded Sometimes?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Sometimes Instagram videos cannot be downloaded if the account is set to private, the link is broken, or the post has been deleted by the owner. Ensure the post is public."
      }
    },
    {
      "@type": "Question",
      "name": "What is the Best Instagram Video Downloader?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Free Downloader is considered one of the best Instagram video downloader tools because it is 100% free, requires no app installation, and supports HD video downloads without any watermarks."
      }
    }
  ]
};

// Inject the structured data into the page head
const script = document.createElement('script');
script.type = "application/ld+json";
script.text = JSON.stringify(faqData);
document.head.appendChild(script);
