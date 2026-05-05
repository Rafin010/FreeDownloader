import re

filepath = r"e:\_free downloader Projext\yt_d\templates\index.html"

with open(filepath, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Fix scroll snapping (remove smooth scroll from html class and add instant scrollTo)
html = html.replace('class="scroll-smooth"', '')
html = html.replace('window.scrollTo({ top: 0 });', 'window.scrollTo(0, 0);')

# 2. Add history and algorithm
algo_js = """
        // --- ALGORITHM & HISTORY ---
        let watchHistory = JSON.parse(localStorage.getItem('yt_watchHistory')) || [];

        function saveToHistory(video) {
            if (typeof video !== 'object') return;
            // Prevent duplicates
            watchHistory = watchHistory.filter(v => v.id !== video.id);
            watchHistory.unshift({id: video.id, title: video.title});
            if (watchHistory.length > 15) watchHistory.pop();
            localStorage.setItem('yt_watchHistory', JSON.stringify(watchHistory));
        }
"""

if "// --- ALGORITHM & HISTORY ---" not in html:
    html = html.replace('const state = {', algo_js + '\n        const state = {')


# 3. Save to history inside showPlayerView
if "saveToHistory(videoInfo);" not in html:
    html = html.replace("updateSEO(videoInfo.title, videoInfo.title, videoInfo.thumbnail, state.currentVideoId);", "updateSEO(videoInfo.title, videoInfo.title, videoInfo.thumbnail, state.currentVideoId);\n                saveToHistory(videoInfo);")


# 4. Modify loadTrendingFeed to use the algorithm
old_trending_fetch = r"const res = await fetch\('/api/trending\?region=US'\);"
new_trending_fetch = """
                let url = '/api/trending?region=US';
                // User Algorithm: 60% chance to show personalized content if history exists
                if (watchHistory.length > 0 && Math.random() > 0.4) {
                    let randomVid = watchHistory[Math.floor(Math.random() * watchHistory.length)];
                    let words = randomVid.title.replace(/[^a-zA-Z0-9 ]/g, '').split(' ').filter(w => w.length > 3);
                    if (words.length > 0) {
                        let randomWord = words[Math.floor(Math.random() * words.length)];
                        url = `/api/search?q=${encodeURIComponent(randomWord)}`;
                        state.currentMode = 'search';
                        state.lastQuery = randomWord;
                    }
                }
                const res = await fetch(url);
"""
html = re.sub(old_trending_fetch, new_trending_fetch, html)


# 5. Make sure the 'fetchNextPage' correctly handles the mode
# In my previous script I injected fetchNextPage. Let's make sure it handles both properly.
# Actually, the user's infinite scroll will just trigger fetchNextPage which respects state.currentMode.
# But wait, in the previous script I injected:
#            if (state.currentQuery) {
#                endpoint = `/api/search?q=${encodeURIComponent(state.currentQuery)}&pageToken=${state.nextPageToken}`;
#            }
# I used `state.currentQuery` but `handleSearch` sets `state.lastQuery`.
# Let's fix that in fetchNextPage:
html = html.replace('state.currentQuery', 'state.lastQuery')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated index.html with Algorithm and Instant Scroll.")
