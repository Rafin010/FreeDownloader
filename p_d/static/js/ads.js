/**
 * Adsterra Ad Integration Script - FreeDownloader Ecosystem
 * Implement this universally across subdomains where needed.
 */

(function() {
    // -------------------------------------------------------------
    // Adsterra Configuration Placeholders
    // REPLACE THESE WITH REAL URLS FROM YOUR ADSTERRA DASHBOARD
    // -------------------------------------------------------------
    window.AD_CONFIG = {
        POP_UNDER_URL: 'https://YOUR_POP_UNDER_URL_HERE',
        DIRECT_LINK_URL: 'https://YOUR_DIRECT_LINK_URL_HERE'
    };

    // 1. POP-UNDER / ON-CLICK AD IMPLEMENTATION
    // Opens an ad on the first interaction anywhere on the page
    let popUnderTriggered = false;

    function triggerPopUnder(e) {
        if (!popUnderTriggered && window.AD_CONFIG.POP_UNDER_URL.includes("http")) {
            // Check if it's an A tag that shouldn't open an ad
            if (e.target.tagName && e.target.tagName.toLowerCase() === 'a' && e.target.target !== '_blank') {
               return; // Let normal links work. 
            }
            
            popUnderTriggered = true;
            
            // For a true pop-under, we open a new window and refocus the current window
            // Modern browsers often block this if not directly tied to a user event,
            // but this is the standard approach network tags use.
            const newWin = window.open(window.AD_CONFIG.POP_UNDER_URL, '_blank');
            if (newWin) {
                // Attempt to bring the main window back into focus (making the ad a pop-under)
                window.focus();
            }

            // Optional: Remove listener after triggering so it doesn't annoy the user on every click
            document.removeEventListener('click', triggerPopUnder);
            document.removeEventListener('paste', triggerPopUnder);
        }
    }

    // Attach to common user interaction events (document click, text box paste)
    document.addEventListener('click', triggerPopUnder, { capture: true, once: false });
    document.addEventListener('paste', triggerPopUnder, { capture: true, once: false });

    // 2. DIRECT LINK ON DOWNLOAD BUTTONS
    // Used specifically for triggering ads when secondary download buttons are clicked.
    // Ensure download buttons have the class `direct-ad-trigger` to use this logic automatically.
    document.addEventListener('click', function(e) {
        if (e.target.closest('.direct-ad-trigger')) {
            if (window.AD_CONFIG.DIRECT_LINK_URL.includes("http")) {
                window.open(window.AD_CONFIG.DIRECT_LINK_URL, '_blank');
            }
        }
    });

})();
