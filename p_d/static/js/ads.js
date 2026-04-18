// AD SCRIPT DISABLED /**
// AD SCRIPT DISABLED  * Adsterra Ad Integration Script - FreeDownloader Ecosystem
// AD SCRIPT DISABLED  * Implement this universally across subdomains where needed.
// AD SCRIPT DISABLED  */
// AD SCRIPT DISABLED 
// AD SCRIPT DISABLED (function() {
// AD SCRIPT DISABLED     // -------------------------------------------------------------
// AD SCRIPT DISABLED     // Adsterra Configuration Placeholders
// AD SCRIPT DISABLED     // REPLACE THESE WITH REAL URLS FROM YOUR ADSTERRA DASHBOARD
// AD SCRIPT DISABLED     // -------------------------------------------------------------
// AD SCRIPT DISABLED     window.AD_CONFIG = {
// AD SCRIPT DISABLED         POP_UNDER_URL: 'https://YOUR_POP_UNDER_URL_HERE',
// AD SCRIPT DISABLED         DIRECT_LINK_URL: 'https://YOUR_DIRECT_LINK_URL_HERE'
// AD SCRIPT DISABLED     };
// AD SCRIPT DISABLED 
// AD SCRIPT DISABLED     // 1. POP-UNDER / ON-CLICK AD IMPLEMENTATION
// AD SCRIPT DISABLED     // Opens an ad on the first interaction anywhere on the page
// AD SCRIPT DISABLED     let popUnderTriggered = false;
// AD SCRIPT DISABLED 
// AD SCRIPT DISABLED     function triggerPopUnder(e) {
// AD SCRIPT DISABLED         if (!popUnderTriggered && window.AD_CONFIG.POP_UNDER_URL.includes("http")) {
// AD SCRIPT DISABLED             // Check if it's an A tag that shouldn't open an ad
// AD SCRIPT DISABLED             if (e.target.tagName && e.target.tagName.toLowerCase() === 'a' && e.target.target !== '_blank') {
// AD SCRIPT DISABLED                return; // Let normal links work. 
// AD SCRIPT DISABLED             }
// AD SCRIPT DISABLED             
// AD SCRIPT DISABLED             popUnderTriggered = true;
// AD SCRIPT DISABLED             
// AD SCRIPT DISABLED             // For a true pop-under, we open a new window and refocus the current window
// AD SCRIPT DISABLED             // Modern browsers often block this if not directly tied to a user event,
// AD SCRIPT DISABLED             // but this is the standard approach network tags use.
// AD SCRIPT DISABLED             const newWin = window.open(window.AD_CONFIG.POP_UNDER_URL, '_blank');
// AD SCRIPT DISABLED             if (newWin) {
// AD SCRIPT DISABLED                 // Attempt to bring the main window back into focus (making the ad a pop-under)
// AD SCRIPT DISABLED                 window.focus();
// AD SCRIPT DISABLED             }
// AD SCRIPT DISABLED 
// AD SCRIPT DISABLED             // Optional: Remove listener after triggering so it doesn't annoy the user on every click
// AD SCRIPT DISABLED             document.removeEventListener('click', triggerPopUnder);
// AD SCRIPT DISABLED             document.removeEventListener('paste', triggerPopUnder);
// AD SCRIPT DISABLED         }
// AD SCRIPT DISABLED     }
// AD SCRIPT DISABLED 
// AD SCRIPT DISABLED     // Attach to common user interaction events (document click, text box paste)
// AD SCRIPT DISABLED     document.addEventListener('click', triggerPopUnder, { capture: true, once: false });
// AD SCRIPT DISABLED     document.addEventListener('paste', triggerPopUnder, { capture: true, once: false });
// AD SCRIPT DISABLED 
// AD SCRIPT DISABLED     // 2. DIRECT LINK ON DOWNLOAD BUTTONS
// AD SCRIPT DISABLED     // Used specifically for triggering ads when secondary download buttons are clicked.
// AD SCRIPT DISABLED     // Ensure download buttons have the class `direct-ad-trigger` to use this logic automatically.
// AD SCRIPT DISABLED     document.addEventListener('click', function(e) {
// AD SCRIPT DISABLED         if (e.target.closest('.direct-ad-trigger')) {
// AD SCRIPT DISABLED             if (window.AD_CONFIG.DIRECT_LINK_URL.includes("http")) {
// AD SCRIPT DISABLED                 window.open(window.AD_CONFIG.DIRECT_LINK_URL, '_blank');
// AD SCRIPT DISABLED             }
// AD SCRIPT DISABLED         }
// AD SCRIPT DISABLED     });
// AD SCRIPT DISABLED 
// AD SCRIPT DISABLED })();
// AD SCRIPT DISABLED 