/**
 * Free Store Remote Popup SDK
 * Include this script in your apps to enable remote-controlled popups.
 */

(function() {
    const API_BASE = 'https://admin.freedownloader.top/api/popup';
    // Fallback to localhost if testing locally
    const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    const API_URL = isLocal ? 'http://127.0.0.1:8000/api/popup' : API_BASE;
    
    // Generate simple stable user ID if not exists
    let userId = localStorage.getItem('fs_popup_uid');
    if (!userId) {
        userId = 'uid_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('fs_popup_uid', userId);
    }

    // You can set window.FS_CATEGORY = 'web' before loading this script
    const category = window.FS_CATEGORY || 'web';

    async function checkPopup() {
        try {
            const res = await fetch(`${API_URL}/check?user_id=${userId}&category=${category}`);
            const data = await res.json();
            
            if (data.id) {
                renderPopup(data);
                logInteraction(data.id, 'shown');
            }
        } catch (err) {
            console.error('[PopupSDK] Check failed', err);
        }
    }

    async function logInteraction(campaignId, action) {
        try {
            await fetch(`${API_URL}/interact`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ campaign_id: campaignId, user_id: userId, action: action })
            });
        } catch (err) { }
    }

    function renderPopup(data) {
        // Create popup overlay
        const overlay = document.createElement('div');
        overlay.id = 'fs-remote-popup';
        overlay.style.cssText = `
            position: fixed; inset: 0; z-index: 999999;
            background: rgba(15, 23, 42, 0.7); backdrop-filter: blur(8px);
            display: flex; align-items: center; justify-content: center;
            font-family: system-ui, -apple-system, sans-serif;
            opacity: 0; transition: opacity 0.3s;
        `;

        const card = document.createElement('div');
        card.style.cssText = `
            background: rgba(30, 41, 59, 0.95);
            border: 1px solid rgba(51, 65, 85, 1);
            border-radius: 20px; padding: 32px; width: 90%; max-width: 400px;
            text-align: center; color: white;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            transform: scale(0.95); transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            position: relative;
        `;

        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '✕';
        closeBtn.style.cssText = `
            position: absolute; top: 16px; right: 16px;
            background: none; border: none; color: #94a3b8;
            font-size: 16px; cursor: pointer; padding: 4px; border-radius: 50%;
        `;
        closeBtn.onclick = () => {
            logInteraction(data.id, 'dismissed');
            overlay.style.opacity = '0';
            setTimeout(() => overlay.remove(), 300);
        };
        card.appendChild(closeBtn);

        const title = document.createElement('h3');
        title.innerText = data.title;
        title.style.cssText = 'margin: 0 0 12px 0; font-size: 21px; font-weight: 800;';
        card.appendChild(title);

        const msg = document.createElement('p');
        msg.innerText = data.message;
        msg.style.cssText = 'margin: 0 0 24px 0; font-size: 14px; color: #cbd5e1; line-height: 1.6;';
        card.appendChild(msg);

        const btn = document.createElement('a');
        btn.innerText = data.button_text;
        btn.href = data.button_url || (isLocal ? 'http://127.0.0.1:8010/donate' : 'https://freedownloader.top/donate');
        btn.target = '_blank';
        btn.style.cssText = `
            display: inline-block; width: 100%;
            background: linear-gradient(to right, #10b981, #3b82f6);
            color: white; font-weight: 700; text-decoration: none;
            padding: 14px 20px; border-radius: 12px; font-size: 14px;
            text-transform: uppercase; letter-spacing: 1px;
            box-shadow: 0 0 15px rgba(16, 185, 129, 0.3);
        `;
        btn.onclick = () => {
            logInteraction(data.id, 'clicked');
            overlay.style.opacity = '0';
            setTimeout(() => overlay.remove(), 300);
        };
        card.appendChild(btn);

        overlay.appendChild(card);
        document.body.appendChild(overlay);

        // Animate in
        requestAnimationFrame(() => {
            overlay.style.opacity = '1';
            card.style.transform = 'scale(1)';
        });
    }

    // Check on load after 3 seconds to avoid blocking main content
    setTimeout(checkPopup, 3000);

})();
