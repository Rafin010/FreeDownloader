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

    // ── Init ─────────────────────────────────────────────────────
    function init() {
        trackPageView();
        sendPing();
        attachDownloadTracking();
        attachAdTracking();
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
