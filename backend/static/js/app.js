/* ═══════════════════════════════════════════
   Free Downloader — Admin Panel JS
   Sidebar + Chart.js + Category Filtering
═══════════════════════════════════════════ */

const API = '';
const REFRESH_MS = 30_000;

let activeSite = '';
let sitesList  = [];

// ── Chart.js dark defaults ────────────────
Chart.defaults.color       = '#6b7280';
Chart.defaults.borderColor = 'rgba(255,255,255,0.04)';
Chart.defaults.font.family = 'Inter, sans-serif';
Chart.defaults.plugins.legend.display = false;

const C = {
    views: '#6366f1', dl: '#10b981', ads: '#f59e0b',
    online: '#3b82f6', sessions: '#d946ef', sites: '#eab308'
};

// ── Official Platform SVG Logos ────────────
const SITE_LOGOS = {
    'yt_downloader': `<svg viewBox="0 0 24 24" class="w-5 h-5" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>`,
    'fb_downloader': `<svg viewBox="0 0 24 24" class="w-5 h-5" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>`,
    'insta_downloader': `<svg viewBox="0 0 24 24" class="w-5 h-5" fill="currentColor"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>`,
    'tiktok_downloader': `<svg viewBox="0 0 24 24" class="w-5 h-5" fill="currentColor"><path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/></svg>`,
    'free_downloader': `<svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>`,
    'porn_downloader': `<svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>`,
};

const SITE_COLORS = {
    'yt_downloader':     { bg: 'bg-red-500/10',     border: 'border-red-500/20',     text: 'text-red-400',     from: 'from-red-500',     to: 'to-red-600' },
    'fb_downloader':     { bg: 'bg-blue-500/10',    border: 'border-blue-500/20',    text: 'text-blue-400',    from: 'from-blue-500',    to: 'to-blue-600' },
    'insta_downloader':  { bg: 'bg-pink-500/10',    border: 'border-pink-500/20',    text: 'text-pink-400',    from: 'from-pink-500',    to: 'to-purple-600' },
    'tiktok_downloader': { bg: 'bg-cyan-500/10',    border: 'border-cyan-500/20',    text: 'text-cyan-400',    from: 'from-cyan-400',    to: 'to-pink-500' },
    'free_downloader':   { bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', text: 'text-emerald-400', from: 'from-emerald-500', to: 'to-teal-500' },
    'porn_downloader':   { bg: 'bg-orange-500/10',  border: 'border-orange-500/20',  text: 'text-orange-400',  from: 'from-orange-500',  to: 'to-red-500' },
};

const DEFAULT_COLOR = { bg: 'bg-indigo-500/10', border: 'border-indigo-500/20', text: 'text-indigo-400', from: 'from-indigo-500', to: 'to-purple-500' };

let dailyChart, doughnutChart, hourlyChart;


// ══════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════
function toast(msg) {
    const el = document.getElementById('toast');
    const txt = document.getElementById('toast-text');
    txt.textContent = msg;
    el.classList.add('toast-show');
    setTimeout(() => el.classList.remove('toast-show'), 3000);
}

function animateNumber(el, target) {
    const start = parseInt(el.textContent.replace(/,/g, '')) || 0;
    const dur = 800;
    let t0;
    const step = (ts) => {
        if (!t0) t0 = ts;
        const p = Math.min((ts - t0) / dur, 1);
        const ease = 1 - Math.pow(1 - p, 3);
        el.textContent = Math.round(start + (target - start) * ease).toLocaleString();
        if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
}

async function apiFetch(path) {
    const res = await fetch(API + path);
    if (!res.ok) throw new Error(`API ${path} → ${res.status}`);
    return res.json();
}

function siteParam() {
    return activeSite ? `?site=${encodeURIComponent(activeSite)}` : '';
}

function hexAlpha(hex, a) {
    const r = parseInt(hex.slice(1,3),16);
    const g = parseInt(hex.slice(3,5),16);
    const b = parseInt(hex.slice(5,7),16);
    return `rgba(${r},${g},${b},${a})`;
}

function esc(s) {
    return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function relTime(ds) {
    const m = Math.floor((Date.now() - new Date(ds).getTime()) / 60000);
    if (m < 1) return 'just now';
    if (m < 60) return `${m}m ago`;
    const h = Math.floor(m / 60);
    if (h < 24) return `${h}h ago`;
    return `${Math.floor(h/24)}d ago`;
}


// ══════════════════════════════════════════
// SIDEBAR — Site Selection
// ══════════════════════════════════════════
function selectSite(siteUrl, siteName) {
    activeSite = siteUrl;

    // Update breadcrumb
    document.getElementById('breadcrumb-site').textContent = siteUrl ? siteName : 'All Sites';

    // Update active banner
    document.getElementById('active-site-name').textContent = siteUrl ? siteName : 'All Sites';

    // Update sidebar active states
    document.querySelectorAll('.sidebar-item').forEach(item => {
        const isActive = item.dataset.site === siteUrl;
        item.classList.toggle('bg-indigo-500/10', isActive);
        item.classList.toggle('text-white', isActive);
        item.classList.toggle('border-indigo-500/20', isActive);
        item.classList.toggle('text-gray-400', !isActive);
        item.classList.toggle('hover:bg-white/5', !isActive);
        item.classList.toggle('hover:text-gray-200', !isActive);
    });

    // Close sidebar on mobile
    if (window.innerWidth < 1024) {
        const sb = document.getElementById('sidebar');
        const ov = document.getElementById('sidebar-overlay');
        sb.classList.remove('sidebar-open');
        ov.classList.add('hidden');
    }

    loadAll();
    toast(siteUrl ? `Viewing: ${siteName}` : 'Viewing: All Sites');
}


async function buildSidebar() {
    const sites = await apiFetch('/api/dashboard/sites');
    sitesList = sites;

    const nav = document.getElementById('sidebar-nav');

    // Keep the "All Sites" button, remove dynamic ones
    const existingItems = nav.querySelectorAll('.sidebar-item-dynamic');
    existingItems.forEach(el => el.remove());

    sites.forEach(s => {
        const color = SITE_COLORS[s.url] || DEFAULT_COLOR;
        const logo  = SITE_LOGOS[s.url] || `<svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/></svg>`;
        const isActive = activeSite === s.url;

        const btn = document.createElement('button');
        btn.className = `sidebar-item sidebar-item-dynamic w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 text-left group ${isActive ? 'bg-indigo-500/10 text-white border border-indigo-500/20' : 'text-gray-400 hover:bg-white/5 hover:text-gray-200'}`;
        btn.dataset.site = s.url;
        btn.onclick = () => selectSite(s.url, s.name);
        btn.innerHTML = `
            <div class="w-9 h-9 rounded-lg ${color.bg} border ${color.border} flex items-center justify-center flex-shrink-0 ${color.text}">
                ${logo}
            </div>
            <div class="flex-1 min-w-0">
                <div class="truncate">${esc(s.name)}</div>
                <div class="text-[11px] text-gray-500 group-hover:text-gray-400">${s.views.toLocaleString()} views</div>
            </div>
            ${s.online_now > 0 ? `<span class="flex items-center gap-1 px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-[10px] font-bold text-emerald-400"><span class="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse"></span>${s.online_now}</span>` : ''}
        `;
        nav.appendChild(btn);
    });
}


// ══════════════════════════════════════════
// STAT CARDS
// ══════════════════════════════════════════
async function loadSummary() {
    const d = await apiFetch('/api/dashboard/summary' + siteParam());
    const map = {
        'stat-views': d.views, 'stat-downloads': d.downloads,
        'stat-ads': d.ad_impressions, 'stat-online': d.online_now,
        'stat-sessions': d.total_sessions, 'stat-sites': d.total_sites
    };
    for (const [id, val] of Object.entries(map)) {
        const el = document.getElementById(id);
        if (el) animateNumber(el, val);
    }
}


// ══════════════════════════════════════════
// DAILY LINE CHART
// ══════════════════════════════════════════
async function loadDailyChart() {
    const d = await apiFetch('/api/dashboard/chart/daily' + siteParam());
    const ctx = document.getElementById('dailyChart');
    if (!ctx) return;

    const data = {
        labels: d.labels,
        datasets: [
            { label: 'Views', data: d.page_views, borderColor: C.views, backgroundColor: hexAlpha(C.views, 0.06), fill: true, tension: 0.4, borderWidth: 2, pointRadius: 2, pointHoverRadius: 5 },
            { label: 'Downloads', data: d.downloads, borderColor: C.dl, backgroundColor: hexAlpha(C.dl, 0.06), fill: true, tension: 0.4, borderWidth: 2, pointRadius: 2, pointHoverRadius: 5 },
            { label: 'Ads', data: d.ad_impressions, borderColor: C.ads, backgroundColor: hexAlpha(C.ads, 0.06), fill: true, tension: 0.4, borderWidth: 2, pointRadius: 2, pointHoverRadius: 5 }
        ]
    };

    if (dailyChart) { dailyChart.data = data; dailyChart.update('active'); }
    else {
        dailyChart = new Chart(ctx, {
            type: 'line', data,
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: {
                    tooltip: { mode: 'index', intersect: false, backgroundColor: '#1a2232', borderColor: '#1f2937', borderWidth: 1, padding: 12, titleColor: '#f3f4f6', bodyColor: '#9ca3af' },
                    legend: { display: false }
                },
                scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.03)' }, ticks: { maxTicksLimit: 10 } },
                    y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.03)' } }
                },
                interaction: { mode: 'nearest', axis: 'x', intersect: false }
            }
        });
    }
}


// ══════════════════════════════════════════
// DOUGHNUT CHART
// ══════════════════════════════════════════
async function loadDoughnutChart() {
    const d = await apiFetch('/api/dashboard/top-events' + siteParam());
    const ctx = document.getElementById('doughnutChart');
    if (!ctx) return;

    const colors = [C.views, C.dl, C.ads, C.online, C.sessions];
    const data = {
        labels: d.labels,
        datasets: [{ data: d.values, backgroundColor: d.labels.map((_, i) => colors[i % colors.length]), borderWidth: 0, hoverOffset: 8 }]
    };

    if (doughnutChart) { doughnutChart.data = data; doughnutChart.update(); }
    else {
        doughnutChart = new Chart(ctx, {
            type: 'doughnut', data,
            options: {
                responsive: true, maintainAspectRatio: false, cutout: '72%',
                plugins: {
                    legend: { display: true, position: 'bottom', labels: { padding: 16, boxWidth: 10, borderRadius: 5, useBorderRadius: true, color: '#9ca3af' } },
                    tooltip: { backgroundColor: '#1a2232', borderColor: '#1f2937', borderWidth: 1, padding: 12, titleColor: '#f3f4f6', bodyColor: '#9ca3af' }
                }
            }
        });
    }
}


// ══════════════════════════════════════════
// HOURLY BAR CHART
// ══════════════════════════════════════════
async function loadHourlyChart() {
    const d = await apiFetch('/api/dashboard/chart/hourly' + siteParam());
    const ctx = document.getElementById('hourlyChart');
    if (!ctx) return;

    const data = {
        labels: d.labels,
        datasets: [
            { label: 'Views', data: d.page_views, backgroundColor: hexAlpha(C.views, 0.65), borderRadius: 6, borderSkipped: false },
            { label: 'Downloads', data: d.downloads, backgroundColor: hexAlpha(C.dl, 0.65), borderRadius: 6, borderSkipped: false }
        ]
    };

    if (hourlyChart) { hourlyChart.data = data; hourlyChart.update(); }
    else {
        hourlyChart = new Chart(ctx, {
            type: 'bar', data,
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false }, tooltip: { mode: 'index', backgroundColor: '#1a2232', borderColor: '#1f2937', borderWidth: 1, padding: 12 } },
                scales: { x: { grid: { display: false } }, y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.03)' } } }
            }
        });
    }
}


// ══════════════════════════════════════════
// SITES TABLE
// ══════════════════════════════════════════
async function loadSitesTable() {
    const sites = sitesList.length ? sitesList : await apiFetch('/api/dashboard/sites');
    const tbody = document.getElementById('sites-tbody');
    if (!tbody) return;

    if (!sites.length) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-gray-600 py-12">No sites registered.</td></tr>`;
        return;
    }

    tbody.innerHTML = sites.map(s => {
        const color = SITE_COLORS[s.url] || DEFAULT_COLOR;
        const logo  = SITE_LOGOS[s.url] || '';
        const isActive = activeSite === s.url;
        return `
        <tr class="border-b border-panel-border hover:bg-white/[0.02] transition-colors ${isActive ? 'bg-indigo-500/5' : ''}">
            <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                    <div class="w-9 h-9 rounded-lg ${color.bg} border ${color.border} flex items-center justify-center flex-shrink-0 ${color.text}">${logo}</div>
                    <div>
                        <div class="font-semibold text-white text-sm">${esc(s.name)}</div>
                        <div class="text-xs text-gray-500">${esc(s.url)}</div>
                    </div>
                </div>
            </td>
            <td class="px-6 py-4"><span class="px-2.5 py-1 bg-indigo-500/10 text-indigo-400 rounded-lg text-xs font-bold">${s.views.toLocaleString()}</span></td>
            <td class="px-6 py-4"><span class="px-2.5 py-1 bg-emerald-500/10 text-emerald-400 rounded-lg text-xs font-bold">${s.downloads.toLocaleString()}</span></td>
            <td class="px-6 py-4"><span class="px-2.5 py-1 bg-amber-500/10 text-amber-400 rounded-lg text-xs font-bold">${s.ad_impressions.toLocaleString()}</span></td>
            <td class="px-6 py-4 text-sm text-gray-300">${s.sessions.toLocaleString()}</td>
            <td class="px-6 py-4">
                <span class="inline-flex items-center gap-1.5 px-2.5 py-1 ${s.online_now > 0 ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-gray-800 text-gray-500 border-gray-700'} border rounded-full text-xs font-semibold">
                    <span class="w-1.5 h-1.5 rounded-full ${s.online_now > 0 ? 'bg-emerald-400 animate-pulse' : 'bg-gray-600'}"></span>
                    ${s.online_now} online
                </span>
            </td>
            <td class="px-6 py-4">
                <button onclick="selectSite('${esc(s.url)}','${esc(s.name)}')"
                    class="px-4 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200
                    ${isActive
                        ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                        : 'bg-white/5 text-gray-400 border border-panel-border hover:bg-indigo-500/10 hover:text-indigo-400 hover:border-indigo-500/30'}">
                    ${isActive ? '✓ Active' : 'View Details'}
                </button>
            </td>
        </tr>`;
    }).join('');
}


// ══════════════════════════════════════════
// SESSIONS TABLE
// ══════════════════════════════════════════
async function loadSessionsTable() {
    const sessions = await apiFetch('/api/dashboard/recent-sessions' + siteParam());
    const tbody = document.getElementById('sessions-tbody');
    if (!tbody) return;

    if (!sessions.length) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-gray-600 py-12">No sessions tracked yet.</td></tr>`;
        return;
    }

    tbody.innerHTML = sessions.map(s => `
        <tr class="border-b border-panel-border hover:bg-white/[0.02] transition-colors">
            <td class="px-5 py-3 font-mono text-xs text-gray-500">${s.session_id.slice(0,14)}…</td>
            <td class="px-5 py-3 text-xs text-gray-300">${esc(s.website_id)}</td>
            <td class="px-5 py-3 text-xs text-gray-400">${esc(s.ip_address||'—')}</td>
            <td class="px-5 py-3"><span class="px-2 py-0.5 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-md text-[11px] font-semibold">${esc(s.category||'general')}</span></td>
            <td class="px-5 py-3 text-xs text-gray-500">${relTime(s.last_active)}</td>
        </tr>
    `).join('');
}


// ══════════════════════════════════════════
// AUTO-REFRESH
// ══════════════════════════════════════════
let countdown = REFRESH_MS / 1000;
const cdEl = document.getElementById('countdown');
setInterval(() => {
    countdown--;
    if (cdEl) cdEl.textContent = countdown;
    if (countdown <= 0) {
        countdown = REFRESH_MS / 1000;
        loadAll();
        toast('Dashboard refreshed');
    }
}, 1000);

async function loadAll() {
    document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
    try {
        await buildSidebar();
        await Promise.all([
            loadSummary(), loadDailyChart(), loadDoughnutChart(),
            loadHourlyChart(), loadSitesTable(), loadSessionsTable()
        ]);
    } catch (e) {
        console.error('[Dashboard]', e);
        toast('⚠ Failed to load — is the server running?');
    }
}

document.getElementById('refresh-btn')?.addEventListener('click', () => {
    countdown = REFRESH_MS / 1000;
    loadAll();
    toast('Refreshing…');
});

document.addEventListener('DOMContentLoaded', loadAll);
