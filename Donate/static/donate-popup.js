/**
 * FreeDownloader — Professional Donation Popup + Notification Widget
 * ==================================================================
 * Features:
 *   - Donation popup (toggle from admin panel)
 *   - Custom notification system (admin can send messages)
 *   - Opens donate page in NEW TAB
 *
 * Usage: <script src="https://freedownloader.top/donate/static/donate-popup.js" defer></script>
 */
(function () {
  'use strict';
  const DONATE_URL = 'https://freedownloader.top/donate';
  const CONFIG_URL = 'https://admin.freedownloader.top/api/popup/config';
  const STORAGE_DISMISS = 'fd_donate_dismissed';
  const STORAGE_NOTIF = 'fd_notif_seen_';
  const SHOW_DELAY_MS = 6000;
  const DISMISS_HOURS = 12;

  // Don't show on the donate page itself
  if (window.location.pathname.includes('/donate')) return;

  // ── CSS ────────────────────────────────────
  function injectCSS() {
    if (document.getElementById('fd-popup-css')) return;
    const style = document.createElement('style');
    style.id = 'fd-popup-css';
    style.textContent = `
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
      #fd-donate-popup, #fd-notif-popup {
        position: fixed; bottom: 24px; right: 24px; z-index: 99999;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        animation: fdPopIn 0.5s cubic-bezier(0.34,1.56,0.64,1) forwards;
        opacity: 0; transform: translateY(30px) scale(0.95);
      }
      #fd-notif-popup { bottom: 24px; right: 24px; }
      @keyframes fdPopIn { to { opacity:1; transform:translateY(0) scale(1); } }
      @keyframes fdPopOut { to { opacity:0; transform:translateY(30px) scale(0.9); } }
      .fd-hiding { animation: fdPopOut 0.35s ease forwards !important; }
      .fd-card {
        background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
        border: 1px solid rgba(59,130,246,0.3);
        border-radius: 20px; padding: 20px; width: 320px;
        max-width: calc(100vw - 32px);
        box-shadow: 0 25px 60px rgba(0,0,0,0.5), 0 0 30px rgba(59,130,246,0.1);
        position: relative; overflow: hidden;
      }
      .fd-card::before {
        content:''; position:absolute; top:0; left:0; right:0; height:3px;
        background: linear-gradient(90deg, #3b82f6, #06b6d4, #8b5cf6);
        border-radius: 20px 20px 0 0;
      }
      .fd-close {
        position:absolute; top:12px; right:12px; width:28px; height:28px;
        background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.1);
        border-radius:50%; color:#94a3b8; cursor:pointer;
        display:flex; align-items:center; justify-content:center;
        transition:all 0.2s; font-size:14px; line-height:1;
      }
      .fd-close:hover { background:rgba(239,68,68,0.15); border-color:rgba(239,68,68,0.4); color:#ef4444; }
      .fd-header { display:flex; align-items:center; gap:12px; margin-bottom:14px; }
      .fd-icon {
        width:42px; height:42px;
        background:linear-gradient(135deg,rgba(59,130,246,0.2),rgba(6,182,212,0.15));
        border:1px solid rgba(59,130,246,0.3); border-radius:14px;
        display:flex; align-items:center; justify-content:center; flex-shrink:0;
      }
      .fd-icon svg { animation: fdPulseHeart 2s ease-in-out infinite; }
      @keyframes fdPulseHeart { 0%,100%{transform:scale(1)} 50%{transform:scale(1.15)} }
      .fd-title { color:#f1f5f9; font-size:15px; font-weight:700; line-height:1.3; }
      .fd-subtitle { color:#64748b; font-size:11px; font-weight:500; letter-spacing:0.05em; text-transform:uppercase; margin-top:2px; }
      .fd-body { color:#94a3b8; font-size:13px; line-height:1.6; margin-bottom:16px; }
      .fd-body strong { color:#e2e8f0; }
      .fd-progress-wrap { background:rgba(255,255,255,0.05); border-radius:999px; height:6px; margin-bottom:8px; overflow:hidden; }
      .fd-progress-bar {
        height:100%; border-radius:999px;
        background:linear-gradient(90deg,#3b82f6,#06b6d4,#3b82f6);
        background-size:200% 100%; animation:fdShimmer 2.5s linear infinite;
        width:68%; transition:width 1.5s ease;
      }
      @keyframes fdShimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
      .fd-stats { display:flex; justify-content:space-between; margin-bottom:16px; font-size:11px; color:#64748b; }
      .fd-stats span { display:flex; align-items:center; gap:4px; }
      .fd-dot { width:6px; height:6px; border-radius:50%; background:#22d3ee; animation:fdDotPulse 2s ease-in-out infinite; }
      @keyframes fdDotPulse { 0%,100%{box-shadow:0 0 0 0 rgba(34,211,238,0.5)} 50%{box-shadow:0 0 0 5px rgba(34,211,238,0)} }
      .fd-cta {
        display:flex; width:100%; align-items:center; justify-content:center; gap:8px;
        padding:12px 20px; background:linear-gradient(135deg,#3b82f6,#2563eb);
        color:#fff; font-weight:700; font-size:13px; letter-spacing:0.06em;
        text-transform:uppercase; border:none; border-radius:12px; cursor:pointer;
        transition:all 0.3s; text-decoration:none;
        box-shadow:0 8px 20px rgba(59,130,246,0.3);
      }
      .fd-cta:hover { background:linear-gradient(135deg,#2563eb,#1d4ed8); box-shadow:0 12px 30px rgba(59,130,246,0.45); transform:translateY(-2px); }
      .fd-secure { display:flex; align-items:center; justify-content:center; gap:5px; margin-top:10px; font-size:10px; color:#475569; }
      /* Notification specific */
      .fd-notif-card {
        background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
        border: 1px solid rgba(99,102,241,0.3);
        border-radius: 20px; padding: 20px; width: 340px;
        max-width: calc(100vw - 32px);
        box-shadow: 0 25px 60px rgba(0,0,0,0.5), 0 0 30px rgba(99,102,241,0.1);
        position: relative; overflow: hidden;
      }
      .fd-notif-card::before {
        content:''; position:absolute; top:0; left:0; right:0; height:3px;
        background: linear-gradient(90deg, #8b5cf6, #ec4899, #f59e0b);
        border-radius: 20px 20px 0 0;
      }
      .fd-notif-icon {
        width:42px; height:42px;
        background:linear-gradient(135deg,rgba(139,92,246,0.2),rgba(236,72,153,0.15));
        border:1px solid rgba(139,92,246,0.3); border-radius:14px;
        display:flex; align-items:center; justify-content:center; flex-shrink:0;
      }
      .fd-notif-msg { color:#cbd5e1; font-size:13.5px; line-height:1.7; margin:12px 0 0; white-space:pre-wrap; }
      .fd-notif-btn {
        display:inline-flex; align-items:center; gap:6px; margin-top:14px;
        padding:10px 18px; background:linear-gradient(135deg,#8b5cf6,#7c3aed);
        color:#fff; font-weight:700; font-size:12px; letter-spacing:0.05em;
        text-transform:uppercase; border:none; border-radius:10px; cursor:pointer;
        transition:all 0.3s; text-decoration:none;
      }
      .fd-notif-btn:hover { transform:translateY(-2px); box-shadow:0 8px 25px rgba(139,92,246,0.4); }
      @media (max-width:480px) {
        #fd-donate-popup, #fd-notif-popup { bottom:70px; right:12px; left:12px; }
        .fd-card, .fd-notif-card { width:100%; }
      }
    `;
    document.head.appendChild(style);
  }

  // ── DONATION POPUP ────────────────────────
  function createDonatePopup() {
    if (document.getElementById('fd-donate-popup')) return;
    injectCSS();
    const popup = document.createElement('div');
    popup.id = 'fd-donate-popup';
    popup.innerHTML = `
      <div class="fd-card">
        <button class="fd-close" title="Dismiss" aria-label="Close">&times;</button>
        <div class="fd-header">
          <div class="fd-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="#3b82f6">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
            </svg>
          </div>
          <div>
            <div class="fd-title">Support FreeDownloader</div>
            <div class="fd-subtitle">Help Keep Us Free &amp; Ad-Free</div>
          </div>
        </div>
        <div class="fd-body">
          Your <strong>small donation</strong> helps us keep this service running <strong>free for everyone</strong>. Every contribution matters! 💙
        </div>
        <div class="fd-progress-wrap"><div class="fd-progress-bar"></div></div>
        <div class="fd-stats">
          <span><span class="fd-dot"></span> 68% funded</span>
          <span>$6,820 / $10,000</span>
        </div>
        <a href="${DONATE_URL}" target="_blank" rel="noopener noreferrer" class="fd-cta">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
          </svg>
          Donate Now
        </a>
        <div class="fd-secure">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <rect x="3" y="11" width="18" height="11" rx="2"/>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
          </svg>
          SSL Secured · Opens in new tab
        </div>
      </div>
    `;
    document.body.appendChild(popup);
    popup.querySelector('.fd-close').addEventListener('click', function (e) {
      e.preventDefault();
      popup.classList.add('fd-hiding');
      localStorage.setItem(STORAGE_DISMISS, Date.now().toString());
      setTimeout(function () { popup.remove(); }, 400);
    });
  }

  // ── NOTIFICATION POPUP ────────────────────
  function createNotifPopup(notif) {
    if (document.getElementById('fd-notif-popup')) return;
    injectCSS();
    const popup = document.createElement('div');
    popup.id = 'fd-notif-popup';
    const hasBtn = notif.button_text && notif.button_url;
    popup.innerHTML = `
      <div class="fd-notif-card">
        <button class="fd-close" title="Close" aria-label="Close">&times;</button>
        <div class="fd-header">
          <div class="fd-notif-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" stroke-width="2">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
            </svg>
          </div>
          <div>
            <div class="fd-title">${notif.title || 'Notification'}</div>
            <div class="fd-subtitle">From FreeDownloader</div>
          </div>
        </div>
        <div class="fd-notif-msg">${notif.message}</div>
        ${hasBtn ? `<a href="${notif.button_url}" target="_blank" rel="noopener" class="fd-notif-btn">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
            <polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
          </svg>
          ${notif.button_text}
        </a>` : ''}
      </div>
    `;
    document.body.appendChild(popup);
    popup.querySelector('.fd-close').addEventListener('click', function (e) {
      e.preventDefault();
      popup.classList.add('fd-hiding');
      localStorage.setItem(STORAGE_NOTIF + notif.id, Date.now().toString());
      setTimeout(function () { popup.remove(); }, 400);
    });
  }

  // ── MAIN: Fetch config from admin API ─────
  async function init() {
    try {
      const resp = await fetch(CONFIG_URL, { mode: 'cors' });
      if (!resp.ok) throw new Error('Config unavailable');
      const cfg = await resp.json();

      // 1) Show notification if admin sent one
      if (cfg.notification && cfg.notification.id) {
        const n = cfg.notification;
        const seen = localStorage.getItem(STORAGE_NOTIF + n.id);
        if (!seen) {
          setTimeout(function () { createNotifPopup(n); }, SHOW_DELAY_MS);
          return; // Don't show donate popup at the same time
        }
      }

      // 2) Show donation popup if enabled by admin
      const mode = cfg.donate_popup_mode || (cfg.donate_popup_enabled ? 'all_time' : 'off');
      if (mode === 'off' && !cfg.donate_popup_enabled) return;

      let shouldShow = false;
      if (mode === 'specific_dates') {
        const today = new Date().getDate();
        const startDay = cfg.donate_popup_start_day || 1;
        const endDay = cfg.donate_popup_end_day || 3;
        if (today >= startDay && today <= endDay) {
          shouldShow = true;
        }
      } else {
        shouldShow = true;
      }

      if (shouldShow) {
        let ignoreDismiss = false;
        if (cfg.donate_push_id) {
          const lastPush = localStorage.getItem('fd_last_push_id');
          if (lastPush !== cfg.donate_push_id) {
            ignoreDismiss = true;
            localStorage.setItem('fd_last_push_id', cfg.donate_push_id);
          }
        }

        if (!ignoreDismiss) {
          const dismissed = localStorage.getItem(STORAGE_DISMISS);
          if (dismissed) {
            const diff = Date.now() - parseInt(dismissed, 10);
            if (diff < DISMISS_HOURS * 60 * 60 * 1000) return;
          }
        }
        setTimeout(createDonatePopup, SHOW_DELAY_MS);
      }
    } catch (e) {
      // Fallback: If admin API is unreachable, show donate popup by default
      const dismissed = localStorage.getItem(STORAGE_DISMISS);
      if (dismissed) {
        const diff = Date.now() - parseInt(dismissed, 10);
        if (diff < DISMISS_HOURS * 60 * 60 * 1000) return;
      }
      setTimeout(createDonatePopup, SHOW_DELAY_MS);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
