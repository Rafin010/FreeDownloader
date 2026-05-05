import re

filepath = r"e:\_free downloader Projext\yt_d\templates\index.html"

with open(filepath, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Background color and text color updates
html = html.replace('bg-white text-gray-900', 'bg-[#0f0f0f] text-gray-100')
html = html.replace('bg-white border-b border-gray-200', 'bg-[#0f0f0f] border-b border-[#272727]')
html = html.replace('bg-white border-r border-gray-200', 'bg-[#0f0f0f] border-r border-[#272727]')
html = html.replace('bg-white', 'bg-[#0f0f0f]')
html = html.replace('text-gray-900', 'text-gray-100')
html = html.replace('text-gray-700', 'text-gray-300')
html = html.replace('text-gray-500', 'text-gray-400')
html = html.replace('bg-gray-50', 'bg-[#222222]')
html = html.replace('hover:bg-gray-100', 'hover:bg-[#333333]')
html = html.replace('border-gray-100', 'border-[#272727]')
html = html.replace('border-gray-300', 'border-[#303030]')
html = html.replace('bg-gray-100', 'bg-[#1a1a1a]')
html = html.replace('bg-gray-200', 'bg-[#272727]')

# 2. Search bar curvature updates
html = html.replace('rounded-l-full', 'rounded-l-xl')
html = html.replace('rounded-r-full', 'rounded-r-xl')

# 3. Add JS for Infinite Scroll and URL Pasting
js_search_code = """
        // ── Search & Infinite Scroll Logic ──
        els.desktopSearch.addEventListener('submit', (e) => {
            e.preventDefault();
            handleSearchInput(document.getElementById('desktop-search-input').value);
        });

        els.mobileSearch.addEventListener('submit', (e) => {
            e.preventDefault();
            handleSearchInput(document.getElementById('mobile-search-input').value);
        });

        function handleSearchInput(query) {
            query = query.trim();
            if (!query) return;

            // Check if URL was pasted
            const isUrl = query.match(/^https?:\\/\\/.*(?:youtube\\.com|youtu\\.be)\\/(?:watch\\?v=|shorts\\/|embed\\/)?([^&?\\s]+)/);
            if (isUrl && isUrl[1]) {
                // It's a YouTube URL, go straight to video
                showPlayerView(isUrl[1]);
                return;
            }

            // Normal search
            performSearch(query);
        }

        let isFetchingNextPage = false;
        let infiniteScrollObserver = null;

        function setupInfiniteScroll() {
            if (infiniteScrollObserver) infiniteScrollObserver.disconnect();
            
            const sentinel = document.createElement('div');
            sentinel.id = 'scroll-sentinel';
            sentinel.className = 'w-full h-10 mt-4 flex items-center justify-center';
            els.videoGrid.parentNode.appendChild(sentinel);

            infiniteScrollObserver = new IntersectionObserver((entries) => {
                if (entries[0].isIntersecting && state.nextPageToken && !isFetchingNextPage) {
                    fetchNextPage();
                }
            }, { rootMargin: '200px' });
            
            infiniteScrollObserver.observe(sentinel);
        }

        async function fetchNextPage() {
            if (!state.nextPageToken || isFetchingNextPage) return;
            isFetchingNextPage = true;
            
            const sentinel = document.getElementById('scroll-sentinel');
            if(sentinel) sentinel.innerHTML = '<i class="fa-solid fa-spinner fa-spin text-xl text-gray-500"></i>';

            let endpoint = '';
            if (state.currentQuery) {
                endpoint = `/api/search?q=${encodeURIComponent(state.currentQuery)}&pageToken=${state.nextPageToken}`;
            } else {
                endpoint = `/api/trending?pageToken=${state.nextPageToken}`;
                if(state.nextRegion) endpoint += `&region=${state.nextRegion}`;
            }

            try {
                const res = await fetch(endpoint);
                const data = await res.json();
                if (data.results && data.results.length > 0) {
                    state.nextPageToken = data.nextPageToken || null;
                    state.nextRegion = data.nextRegion || null;
                    renderVideoGrid(data.results, true); // Append
                } else {
                    state.nextPageToken = null;
                }
            } catch(e) {
                console.error("Infinite scroll error:", e);
            } finally {
                isFetchingNextPage = false;
                if(sentinel) sentinel.innerHTML = '';
            }
        }
"""

# Replace old search submit event listeners
old_search_block = r"els\.desktopSearch\.addEventListener\('submit', \(e\) => \{.*?\}\);"
html = re.sub(old_search_block, '', html, flags=re.DOTALL)
old_mobile_search_block = r"els\.mobileSearch\.addEventListener\('submit', \(e\) => \{.*?\}\);"
html = re.sub(old_mobile_search_block, '', html, flags=re.DOTALL)

# Insert the new JS logic before the loadInitialFeed function
html = html.replace('async function loadInitialFeed() {', js_search_code + '\n        async function loadInitialFeed() {')

# Modify loadInitialFeed to setup infinite scroll
html = html.replace('renderVideoGrid(data.results);', 'renderVideoGrid(data.results);\n                    state.nextPageToken = data.nextPageToken || null;\n                    state.nextRegion = data.nextRegion || null;\n                    setupInfiniteScroll();')

# Modify performSearch to setup infinite scroll
html = html.replace('renderVideoGrid(data.results);', 'renderVideoGrid(data.results);\n                    state.nextPageToken = data.nextPageToken || null;\n                    state.nextRegion = data.nextRegion || null;\n                    setupInfiniteScroll();')


with open(filepath, 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated HTML.")
