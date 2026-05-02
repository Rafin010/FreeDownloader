/**
 * ╔══════════════════════════════════════════════════════════════╗
 * ║           Free Downloader — Analytics Tracker v2.0          ║
 * ║  Drop this script on any page to start tracking instantly.  ║
 * ║                                                              ║
 * ║  Usage:                                                      ║
 * ║  <script                                                     ║
 * ║    src="https://YOUR_BACKEND/static/tracker.js"             ║
 * ║    data-site-id="tiktok_downloader"                         ║
 * ║    data-category="general"                                   ║
 * ║    data-backend-url="https://analytics.freedownloader.top"  ║
 * ║  ></script>                                                  ║
 * ╚══════════════════════════════════════════════════════════════╝
 */

(function () {
    'use strict';

    // ── Config ──────────────────────────────────────────────────
    const scriptTag  = document.currentScript ||
        document.querySelector('script[data-site-id]');

    // Backend URL: read from data-attribute, fallback to same origin
    const BACKEND_URL  = scriptTag?.dataset?.backendUrl || window.location.origin;
    const PING_INTERVAL = 30_000;                   // 30 s heartbeat

    // ── Derive site-id from script tag attribute ─────────────────
    const WEBSITE_ID = scriptTag?.dataset?.siteId  || window.location.origin;
    const CATEGORY   = scriptTag?.dataset?.category || 'general';

    // ── Cookie Helpers ──────────────────────────────────────────
    function setCookie(name, value, days) {
        let expires = '';
        if (days) {
            const date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            expires = '; expires=' + date.toUTCString();
        }
        // Use SameSite=Lax for cross-subdomain compatibility
        document.cookie = name + '=' + encodeURIComponent(value) + expires + '; path=/; SameSite=Lax';
    }

    function getCookie(name) {
        const nameEQ = name + '=';
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            let c = cookies[i].trim();
            if (c.indexOf(nameEQ) === 0) {
                return decodeURIComponent(c.substring(nameEQ.length));
            }
        }
        return null;
    }

    // ── Persistent User ID (Cookie — 1 year) ────────────────────
    const UID_COOKIE = 'fdl_uid';
    let userId = getCookie(UID_COOKIE);
    if (!userId) {
        userId = 'uid_' + Math.random().toString(36).slice(2, 10) + '_' + Date.now();
        setCookie(UID_COOKIE, userId, 365);
    }

    // ── Category Preferences Cookie ─────────────────────────────
    const PREFS_COOKIE = 'fdl_prefs';
    function getPreferences() {
        const raw = getCookie(PREFS_COOKIE);
        if (!raw) return {};
        try { return JSON.parse(raw); } catch(e) { return {}; }
    }

    function updatePreferences(category, eventType) {
        const prefs = getPreferences();
        if (!prefs[category]) {
            prefs[category] = { views: 0, downloads: 0, last_visit: null };
        }
        if (eventType === 'page_view') prefs[category].views++;
        if (eventType === 'download') prefs[category].downloads++;
        prefs[category].last_visit = new Date().toISOString();
        setCookie(PREFS_COOKIE, JSON.stringify(prefs), 365);
        return prefs;
    }

    // ── Session ID (persisted in localStorage) ───────────────────
    const SESSION_KEY = '_fdl_session';
    let sessionId = localStorage.getItem(SESSION_KEY);
    if (!sessionId) {
        sessionId = 'sess_' + Math.random().toString(36).slice(2, 10) +
                    '_' + Date.now();
        localStorage.setItem(SESSION_KEY, sessionId);
    }

    // ── Helpers ──────────────────────────────────────────────────
    function post(path, body) {
        return fetch(BACKEND_URL + path, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify(body),
            keepalive: true
        }).catch(() => {});  // silently fail — never break the host page
    }

    function sendEvent(eventType, extra = {}) {
        // Update category preferences
        const prefs = updatePreferences(CATEGORY, eventType);

        return post('/api/event', {
            session_id:  sessionId,
            website_id:  WEBSITE_ID,
            event_type:  eventType,
            category:    CATEGORY,
            cookie_id:   userId,
            preferences: prefs,
            meta:        extra
        });
    }

    function sendPing() {
        return post('/api/ping', {
            session_id: sessionId,
            website_id: WEBSITE_ID,
            cookie_id:  userId
        });
    }

    // ── Track page view ──────────────────────────────────────────
    function trackPageView() {
        sendEvent('page_view', { url: window.location.href, referrer: document.referrer });
    }

    // ── Track download button clicks ─────────────────────────────
    // Any element with data-track="download" or class "download-btn"
    function attachDownloadTracking() {
        document.addEventListener('click', function (e) {
            const el = e.target.closest('[data-track="download"], .download-btn, a[download]');
            if (el) {
                sendEvent('download', {
                    label: el.textContent?.trim().slice(0, 80),
                    href:  el.href || el.dataset.href || ''
                });
            }
        }, true);
    }

    // ── Track ad impressions ─────────────────────────────────────
    // Observe elements with data-track="ad" or class "tracker-ad"
    function attachAdTracking() {
        if (!('IntersectionObserver' in window)) return;

        const seen = new WeakSet();
        const observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting && !seen.has(entry.target)) {
                    seen.add(entry.target);
                    sendEvent('ad_impression', {
                        ad_id: entry.target.dataset.adId || 'unknown'
                    });
                }
            });
        }, { threshold: 0.5 });

        function observeAds() {
            document.querySelectorAll('[data-track="ad"], .tracker-ad').forEach(function (el) {
                if (!seen.has(el)) observer.observe(el);
            });
        }

        observeAds();

        // Also watch for dynamically injected ads
        const mutObs = new MutationObserver(observeAds);
        mutObs.observe(document.body, { childList: true, subtree: true });
    }

    // ── Fetch and Show Popup ─────────────────────────────────────
    function loadPopup() {
        const url = BACKEND_URL + '/api/popup/check?user_id=' + encodeURIComponent(userId) + '&category=' + encodeURIComponent(CATEGORY);
        fetch(url).then(r => r.json()).then(data => {
            if (data.id) {
                showPopup(data);
            }
        }).catch(() => {});
    }

    function showPopup(campaign) {
        // Log shown
        post('/api/popup/interact', {
            campaign_id: campaign.id,
            user_id: userId,
            action: 'shown'
        });

        const pop = document.createElement('div');
        pop.id = 'fdl-popup-container';
        pop.innerHTML = `
            <div style="position:fixed;bottom:20px;left:20px;z-index:999999;width:320px;max-width:calc(100vw - 40px);
                        background:rgba(15,23,42,0.85);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);
                        border:1px solid rgba(59,130,246,0.3);border-radius:20px;padding:24px;
                        box-shadow:0 25px 50px -12px rgba(0,0,0,0.5);color:#fff;font-family:system-ui,sans-serif;
                        transform:translateY(20px);opacity:0;transition:all 0.5s cubic-bezier(0.16, 1, 0.3, 1);">
                <button id="fdl-pop-close" style="position:absolute;top:12px;right:12px;background:none;border:none;color:#64748b;cursor:pointer;padding:4px;">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
                </button>
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
                    <div style="width:36px;height:36px;border-radius:10px;background:rgba(59,130,246,0.15);display:flex;align-items:center;justify-content:center;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
                    </div>
                    <h3 style="margin:0;font-size:1.05rem;font-weight:700;color:#e2e8f0;">${esc(campaign.title)}</h3>
                </div>
                <p style="margin:0 0 16px 0;font-size:0.85rem;line-height:1.5;color:#94a3b8;">${esc(campaign.message)}</p>
                <button id="fdl-pop-btn" style="width:100%;padding:10px;border-radius:10px;background:linear-gradient(135deg,#3b82f6,#06b6d4);color:#fff;border:none;font-weight:600;font-size:0.85rem;cursor:pointer;transition:transform 0.2s;box-shadow:0 8px 20px rgba(59,130,246,0.25);">
                    ${esc(campaign.button_text || 'Learn More')}
                </button>
            </div>
        `;
        document.body.appendChild(pop);
        
        const popEl = pop.firstElementChild;
        // Trigger animation
        requestAnimationFrame(() => {
            popEl.style.transform = 'translateY(0)';
            popEl.style.opacity = '1';
        });

        document.getElementById('fdl-pop-close').addEventListener('click', () => {
            popEl.style.transform = 'translateY(20px)';
            popEl.style.opacity = '0';
            setTimeout(() => pop.remove(), 500);
            post('/api/popup/interact', { campaign_id: campaign.id, user_id: userId, action: 'dismissed' });
        });

        document.getElementById('fdl-pop-btn').addEventListener('click', () => {
            post('/api/popup/interact', { campaign_id: campaign.id, user_id: userId, action: 'clicked' });
            let targetUrl = campaign.button_url;
            if (!targetUrl || targetUrl.trim() === '') {
                targetUrl = 'https://freedownloader.top/donate';
            }
            window.location.href = targetUrl;
        });
    }

    // ── Init ─────────────────────────────────────────────────────
    function init() {
        trackPageView();
        sendPing();
        attachDownloadTracking();
        attachAdTracking();
        loadPopup();
        setInterval(sendPing, PING_INTERVAL);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Expose for manual use: FDLTracker.track('download', {...})
    window.FDLTracker = {
        track: sendEvent,
        ping: sendPing,
        getUserId: function() { return userId; },
        getPreferences: getPreferences
    };

})();
