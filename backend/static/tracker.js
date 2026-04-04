/**
 * ╔══════════════════════════════════════════════════════════════╗
 * ║           Free Downloader — Analytics Tracker v1.0          ║
 * ║  Drop this script on any page to start tracking instantly.  ║
 * ║                                                              ║
 * ║  Usage:                                                      ║
 * ║  <script                                                     ║
 * ║    src="https://YOUR_BACKEND/static/tracker.js"             ║
 * ║    data-site-id="https://your-site.com"                     ║
 * ║    data-category="general"                                   ║
 * ║  ></script>                                                  ║
 * ╚══════════════════════════════════════════════════════════════╝
 */

(function () {
    'use strict';

    // ── Config ──────────────────────────────────────────────────
    const BACKEND_URL  = 'http://localhost:5000';   // change to deployed URL
    const PING_INTERVAL = 30_000;                   // 30 s heartbeat

    // ── Derive site-id from script tag attribute ─────────────────
    const scriptTag  = document.currentScript ||
        document.querySelector('script[data-site-id]');
    const WEBSITE_ID = scriptTag?.dataset?.siteId  || window.location.origin;
    const CATEGORY   = scriptTag?.dataset?.category || 'general';

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
        return post('/api/event', {
            session_id: sessionId,
            website_id: WEBSITE_ID,
            event_type: eventType,
            category:   CATEGORY,
            meta:       extra
        });
    }

    function sendPing() {
        return post('/api/ping', {
            session_id: sessionId,
            website_id: WEBSITE_ID
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
    window.FDLTracker = { track: sendEvent, ping: sendPing };

})();
