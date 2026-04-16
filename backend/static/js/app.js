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

    // View toggling
    document.getElementById('view-freestore')?.classList.add('hidden');
    document.getElementById('view-dashboard')?.classList.remove('hidden');
    document.getElementById('view-dashboard')?.classList.add('block');

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

function showFreeStore() {
    activeSite = 'freestore';
    
    // View toggling
    document.getElementById('view-dashboard')?.classList.add('hidden');
    document.getElementById('view-dashboard')?.classList.remove('block');
    document.getElementById('view-freestore')?.classList.remove('hidden');
    document.getElementById('view-freestore')?.classList.add('block');

    document.getElementById('breadcrumb-site').textContent = 'Free Store';
    document.getElementById('active-site-name').textContent = 'Free Store';

    // Update sidebar active states
    document.querySelectorAll('.sidebar-item').forEach(item => {
        const isActive = item.id === 'btn-free-store';
        item.classList.toggle('bg-emerald-500/10', isActive);
        item.classList.toggle('text-white', isActive);
        item.classList.toggle('border-emerald-500/20', isActive);
        item.classList.toggle('text-gray-400', !isActive);
        item.classList.toggle('hover:bg-white/5', !isActive);
        item.classList.toggle('hover:text-gray-200', !isActive);
        
        // Handle selectSite active classes removal
        if(isActive) {
            item.classList.remove('bg-indigo-500/10', 'border-indigo-500/20');
        }
    });

    if (window.innerWidth < 1024) {
        document.getElementById('sidebar').classList.remove('sidebar-open');
        document.getElementById('sidebar-overlay').classList.add('hidden');
    }
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
    const canvas = document.getElementById('dailyChart');
    if (!canvas) return;

    // Calculate 30-day totals and update UI
    const tViews = d.page_views.reduce((a, b) => a + b, 0);
    const tDls = d.downloads.reduce((a, b) => a + b, 0);
    const tAds = d.ad_impressions.reduce((a, b) => a + b, 0);

    const elViews = document.getElementById('trend-total-views');
    const elDls = document.getElementById('trend-total-dls');
    const elAds = document.getElementById('trend-total-ads');

    if (elViews) animateNumber(elViews, tViews);
    if (elDls) animateNumber(elDls, tDls);
    if (elAds) animateNumber(elAds, tAds);

    // Create Gradients for Professional Look
    const ctx = canvas.getContext('2d');
    const gradViews = ctx.createLinearGradient(0, 0, 0, 300);
    gradViews.addColorStop(0, hexAlpha(C.views, 0.4));
    gradViews.addColorStop(1, hexAlpha(C.views, 0.01));

    const gradDl = ctx.createLinearGradient(0, 0, 0, 300);
    gradDl.addColorStop(0, hexAlpha(C.dl, 0.4));
    gradDl.addColorStop(1, hexAlpha(C.dl, 0.01));

    const gradAds = ctx.createLinearGradient(0, 0, 0, 300);
    gradAds.addColorStop(0, hexAlpha(C.ads, 0.4));
    gradAds.addColorStop(1, hexAlpha(C.ads, 0.01));

    const data = {
        labels: d.labels,
        datasets: [
            { 
                label: 'Views', data: d.page_views, 
                borderColor: C.views, backgroundColor: gradViews, 
                fill: true, tension: 0.4, borderWidth: 3, 
                pointRadius: 0, pointHoverRadius: 6, pointHoverBackgroundColor: C.views, pointHoverBorderColor: '#ffffff', pointHoverBorderWidth: 2
            },
            { 
                label: 'Downloads', data: d.downloads, 
                borderColor: C.dl, backgroundColor: gradDl, 
                fill: true, tension: 0.4, borderWidth: 3, 
                pointRadius: 0, pointHoverRadius: 6, pointHoverBackgroundColor: C.dl, pointHoverBorderColor: '#ffffff', pointHoverBorderWidth: 2
            },
            { 
                label: 'Ads', data: d.ad_impressions, 
                borderColor: C.ads, backgroundColor: gradAds, 
                fill: true, tension: 0.4, borderWidth: 3, 
                pointRadius: 0, pointHoverRadius: 6, pointHoverBackgroundColor: C.ads, pointHoverBorderColor: '#ffffff', pointHoverBorderWidth: 2
            }
        ]
    };

    if (dailyChart) { dailyChart.data = data; dailyChart.update('active'); }
    else {
        dailyChart = new Chart(canvas, {
            type: 'line', data,
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: {
                    tooltip: { 
                        mode: 'index', intersect: false, 
                        backgroundColor: '#111827', borderColor: '#374151', borderWidth: 1, 
                        padding: 12, titleColor: '#f9fafb', bodyColor: '#d1d5db',
                        titleFont: { size: 13, weight: 'bold' },
                        bodyFont: { size: 12 },
                        boxPadding: 4,
                        usePointStyle: true, pointStyle: 'circle'
                    },
                    legend: { display: false }
                },
                scales: {
                    x: { 
                        grid: { display: false, drawBorder: false }, 
                        ticks: { color: '#6b7280', font: { size: 11 }, maxTicksLimit: 10 } 
                    },
                    y: { 
                        beginAtZero: true, 
                        grid: { color: 'rgba(255,255,255,0.05)', borderDash: [4, 4], drawBorder: false },
                        ticks: { color: '#6b7280', font: { size: 11 }, padding: 10 }
                    }
                },
                interaction: { mode: 'index', intersect: false }
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
            loadHourlyChart(), loadSitesTable(), loadSessionsTable(),
            loadActiveInstalls(), loadStoreItems(), loadPopups()
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

// ══════════════════════════════════════════
// FREE STORE & POPUP MANAGEMENT
// ══════════════════════════════════════════
async function loadActiveInstalls() {
    try {
        const data = await apiFetch('/api/install/stats');
        const tb = document.getElementById('installs-tbody');
        document.getElementById('stat-active-installs').textContent = data.total_active || 0;
        
        if (!data.breakdown || !data.breakdown.length) {
            tb.innerHTML = '<tr><td colspan="3" class="text-center text-gray-600 py-8">No active installs.</td></tr>';
            return;
        }
        
        tb.innerHTML = data.breakdown.map(i => `
            <tr class="border-b border-panel-border hover:bg-white/[0.02]">
                <td class="px-6 py-4 text-xs font-semibold text-white">${esc(i.software_name)}</td>
                <td class="px-6 py-4 text-xs text-gray-400">${i.total_installs}</td>
                <td class="px-6 py-4 text-xs font-bold text-emerald-400">${i.active_installs}</td>
            </tr>
        `).join('');
    } catch(e) {}
}

async function loadStoreItems() {
    try {
        const items = await apiFetch('/api/store/items');
        const tb = document.getElementById('store-items-tbody');
        if (!items || !items.length) {
            tb.innerHTML = '<tr><td colspan="5" class="text-center text-gray-600 py-8">No items found.</td></tr>';
            return;
        }
        tb.innerHTML = items.map(i => `
            <tr class="border-b border-panel-border hover:bg-white/[0.02] ${!i.is_active ? 'opacity-50' : ''}" id="store-row-${i.id}">
                <td class="px-4 py-3">
                    <div class="flex items-center gap-2">
                        ${i.icon_url ? `<img src="${esc(i.icon_url)}" class="w-8 h-8 rounded-lg object-cover border border-slate-700" onerror="this.style.display='none'">` : ''}
                        <div>
                            <div class="text-xs font-semibold text-white">${esc(i.title)}</div>
                            <div class="text-[10px] text-gray-500">${esc(i.slug)}</div>
                        </div>
                    </div>
                </td>
                <td class="px-4 py-3"><span class="px-2 py-1 bg-indigo-500/10 text-indigo-400 text-[10px] font-bold rounded">${esc(i.category)}</span></td>
                <td class="px-4 py-3">
                    <span class="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-bold ${i.is_active ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}">
                        ${i.is_active ? '<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg> Active' : '<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"></path></svg> Disabled'}
                    </span>
                </td>
                <td class="px-4 py-3 text-xs text-gray-400">${i.download_count || 0}</td>
                <td class="px-4 py-3">
                    <div class="flex items-center gap-1">
                        <button onclick='storeEditItem(${JSON.stringify(i).replace(/'/g, "&#39;")})' title="Edit" class="p-1.5 rounded-lg hover:bg-indigo-500/20 text-gray-400 hover:text-indigo-400 transition-colors">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
                        </button>
                        <button onclick="storeToggleItem(${i.id}, ${i.is_active ? 'false' : 'true'})" title="${i.is_active ? 'Disable' : 'Enable'}" class="p-1.5 rounded-lg hover:bg-amber-500/20 text-gray-400 hover:text-amber-400 transition-colors">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="${i.is_active ? 'M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636' : 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z'}"/></svg>
                        </button>
                        <button onclick="storeDeleteItem(${i.id}, '${esc(i.title)}')" title="Delete" class="p-1.5 rounded-lg hover:bg-red-500/20 text-gray-400 hover:text-red-400 transition-colors">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    } catch(e) {}
}

// ── Store Item Actions ──────────────────────
async function storeToggleItem(id, activate) {
    try {
        const res = await fetch(API + '/api/store/items/' + id, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ is_active: activate })
        });
        if (!res.ok) throw new Error('Failed');
        toast(activate ? ' Item enabled!' : ' Item disabled!');
        loadStoreItems();
    } catch(e) {
        toast('Error: ' + e.message);
    }
}

async function storeDeleteItem(id, title) {
    if (!confirm(`Are you sure you want to DELETE "${title}"?\nThis action cannot be undone.`)) return;
    try {
        const res = await fetch(API + '/api/store/items/' + id, { method: 'DELETE' });
        if (!res.ok) throw new Error('Failed');
        toast(' Item deleted!');
        loadStoreItems();
    } catch(e) {
        toast('Error: ' + e.message);
    }
}

function storeEditItem(item) {
    // Populate form fields with item data
    document.getElementById('store-title').value = item.title || '';
    document.getElementById('store-slug').value = item.slug || '';
    document.getElementById('store-cat').value = item.category || 'software';
    document.getElementById('store-dev').value = item.developer || '';
    document.getElementById('store-version').value = item.version || '1.0.0';
    document.getElementById('store-rating').value = item.rating || 4.5;
    document.getElementById('store-price').value = item.price || 'Free';
    document.getElementById('store-icon').value = item.icon_url || '';
    document.getElementById('store-desc').value = item.description || '';
    document.getElementById('store-long-desc').value = item.long_description || '';
    document.getElementById('store-link').value = item.download_link || '';
    
    // Trigger category change to update UI
    document.getElementById('store-cat').dispatchEvent(new Event('change'));
    
    // Switch form to edit mode
    const form = document.getElementById('store-upload-form');
    const btn = form.querySelector('button[type="submit"]');
    btn.textContent = ' Update Item';
    btn.dataset.editId = item.id;
    
    // Scroll to form
    form.scrollIntoView({ behavior: 'smooth', block: 'start' });
    toast(' Editing: ' + item.title);
}

async function storeUpdateItem(id, data) {
    try {
        const res = await fetch(API + '/api/store/items/' + id, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error('Failed to update');
        toast(' Item updated successfully!');
        loadStoreItems();
        return true;
    } catch(e) {
        toast('Error: ' + e.message);
        return false;
    }
}

async function loadPopups() {
    try {
        const paps = await apiFetch('/api/popup/campaigns');
        const tb = document.getElementById('popups-tbody');
        if (!paps || !paps.length) {
            tb.innerHTML = '<tr><td colspan="4" class="text-center text-gray-600 py-8">No campaigns found.</td></tr>';
            return;
        }
        tb.innerHTML = paps.map(p => `
            <tr class="border-b border-panel-border hover:bg-white/[0.02]">
                <td class="px-4 py-3">
                    <div class="text-xs font-semibold text-white">${esc(p.title)}</div>
                    <div class="text-[10px] text-gray-500">${esc(p.popup_type)} Target: ${esc(p.category_filter||'All')}</div>
                </td>
                <td class="px-4 py-3">
                    <span class="px-2 py-1 rounded text-[10px] font-bold ${p.is_active ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}">${p.is_active ? 'Active' : 'Inactive'}</span>
                </td>
                <td class="px-4 py-3 text-xs text-gray-400">${p.shown_count}</td>
                <td class="px-4 py-3 text-xs font-bold text-indigo-400">${p.click_count}</td>
            </tr>
        `).join('');
    } catch(e) {}
}

// Upload/Update Store Item
document.getElementById('store-upload-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    const isEdit = !!btn.dataset.editId;
    btn.textContent = isEdit ? 'Updating...' : 'Uploading...';
    btn.disabled = true;
    
    try {
        const fileInput = document.getElementById('store-file');
        let filePath = '';
        let fileSize = '';
        
        if (fileInput.files.length > 0) {
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('category', document.getElementById('store-cat').value);
            
            const upRes = await fetch(API + '/api/store/upload', { method: 'POST', body: formData });
            const upData = await upRes.json();
            if (upData.error) throw new Error(upData.error);
            filePath = upData.path;
            fileSize = upData.size;
        }
        
        let iconUrl = document.getElementById('store-icon')?.value?.trim();
        if (iconUrl && !/^https?:\/\//i.test(iconUrl) && !iconUrl.startsWith('/')) {
            iconUrl = 'https://' + iconUrl;
        }
        
        let downloadLink = document.getElementById('store-link')?.value?.trim();
        if (downloadLink && !/^https?:\/\//i.test(downloadLink) && !downloadLink.startsWith('/')) {
            downloadLink = 'https://' + downloadLink;
        }

        const payload = {
            title: document.getElementById('store-title').value,
            slug: document.getElementById('store-slug').value,
            category: document.getElementById('store-cat').value,
            developer: document.getElementById('store-dev')?.value || undefined,
            version: document.getElementById('store-version')?.value || '1.0.0',
            rating: parseFloat(document.getElementById('store-rating')?.value || '0'),
            price: document.getElementById('store-price')?.value || 'Free',
            icon_url: iconUrl || undefined,
            description: document.getElementById('store-desc').value,
            long_description: document.getElementById('store-long-desc')?.value || undefined,
            download_link: downloadLink || undefined,
        };
        if (filePath) {
            payload.file_path = filePath;
            payload.file_size = fileSize;
        }

        if (isEdit) {
            const success = await storeUpdateItem(btn.dataset.editId, payload);
            if (!success) throw new Error('Update failed');
            delete btn.dataset.editId;
        } else {
            const res = await fetch(API + '/api/store/items', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            if (!res.ok) throw new Error('Failed to create item');
            toast(' Store item created successfully!');
        }
        
        e.target.reset();
        document.getElementById('store-cat').dispatchEvent(new Event('change'));
        loadStoreItems();
    } catch (err) {
        if (!isEdit) { toast('Error: ' + err.message); }
    } finally {
        btn.textContent = ' Save & Publish';
        btn.disabled = false;
    }
});

// Create Popup Campaign
document.getElementById('popup-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    btn.textContent = 'Launching...';
    
    try {
        const res = await fetch(API + '/api/popup/campaigns', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                title: document.getElementById('pop-title').value,
                message: document.getElementById('pop-msg').value,
                button_text: document.getElementById('pop-btn').value,
                category_filter: document.getElementById('pop-cat').value || null
            })
        });
        
        if (!res.ok) throw new Error('Failed to create campaign');
        toast('Campaign launched successfully!');
        e.target.reset();
        loadPopups();
    } catch (err) {
        toast('Error: ' + err.message);
    } finally {
        btn.textContent = 'Launch Campaign';
    }
});

document.addEventListener('DOMContentLoaded', () => {
    loadAll();
    
    // Dynamic UI for Category Upload
    const storeCat = document.getElementById('store-cat');
    const storeFileSection = document.getElementById('store-file-section');
    const storeLinkLabel = document.getElementById('store-link-label');
    const storeLinkHelp = document.getElementById('store-link-help');
    const storeInfoText = document.getElementById('store-info-text');
    const storeLink = document.getElementById('store-link');
    
    if (storeCat) {
        const updateFormUI = () => {
            const val = storeCat.value;
            if (val === 'web') {
                if (storeFileSection) storeFileSection.style.display = 'none';
                if (storeLinkLabel) storeLinkLabel.innerHTML = ' Website URL <span class="text-red-400">*</span>';
                if (storeLinkHelp) storeLinkHelp.textContent = 'Provide the full URL of your website (e.g., https://example.com)';
                if (storeInfoText) storeInfoText.textContent = ' Web: web: Provide website URL and icon image link. File upload is not required.';
                if (storeLink) { storeLink.required = true; storeLink.placeholder = 'https://your-website.com'; }
            } else if (val === 'app') {
                if (storeFileSection) storeFileSection.style.display = 'block';
                if (storeLinkLabel) storeLinkLabel.innerHTML = ' Download Link <span class="text-gray-600">(optional)</span>';
                if (storeLinkHelp) storeLinkHelp.textContent = 'Provide an APK/App download link or directly upload the file below.';
                if (storeInfoText) storeInfoText.textContent = ' Provide icon image URL and upload APK file or provide download link for App.';
                if (storeLink) { storeLink.required = false; storeLink.placeholder = 'https://drive.google.com/file/...'; }
            } else {
                if (storeFileSection) storeFileSection.style.display = 'block';
                if (storeLinkLabel) storeLinkLabel.innerHTML = ' Download Link <span class="text-gray-600">(optional)</span>';
                if (storeLinkHelp) storeLinkHelp.textContent = 'Provide software download link or upload file below.';
                if (storeInfoText) storeInfoText.textContent = ' Provide icon image URL and upload .exe/.zip file or provide download link for Software.';
                if (storeLink) { storeLink.required = false; storeLink.placeholder = 'https://drive.google.com/file/...'; }
            }
        };
        storeCat.addEventListener('change', updateFormUI);
        updateFormUI(); // Run once on load
    }
});
