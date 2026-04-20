        // Mobile Menu Script
        const mobileMenuBtn = document.getElementById('mobileMenuBtn');
        const mobileMenu = document.getElementById('mobileMenu');
        
        mobileMenuBtn.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });

        // Downloader Script
        async function pasteFromClipboard() {
            try {
                const text = await navigator.clipboard.readText();
                document.getElementById('videoUrl').value = text;
            } catch (err) {
                showCustomAlert('Browser blocked clipboard access! Please manually paste the link.');
            }
        }

        let currentVideoUrl = "";

        async function fetchVideoInfo() {
            currentVideoUrl = document.getElementById('videoUrl').value.trim();
            if(!currentVideoUrl) {
                showCustomAlert('Please enter a valid video URL first!');
                return;
            }

            document.getElementById('resultSection').classList.add('hidden');
            document.getElementById('loading').classList.remove('hidden');

            try {
                const response = await fetch('/api/get_info', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: currentVideoUrl })
                });
                
                const data = await response.json();
                document.getElementById('loading').classList.add('hidden');

                if(response.ok) {
                    const thumbEl = document.getElementById('videoThumb');
                    thumbEl.referrerPolicy = 'no-referrer';
                    thumbEl.src = data.thumbnail;
                    document.getElementById('videoTitle').innerText = data.title;
                    
                    const resList = document.getElementById('resolutionsList');
                    resList.innerHTML = ''; 
                    
                    data.formats.forEach(q => {
                        const btn = document.createElement('button');
                        btn.className = 'w-full flex justify-between items-center px-4 py-3 border border-gray-200 rounded-lg bg-white hover:bg-blue-50 transition-all duration-300 font-medium text-gray-800 shadow-sm hover:shadow-md transform hover:-translate-y-1 hover-bounce text-sm sm:text-base';
                        
                        btn.innerHTML = `
                            <span class="flex items-center"><i class="fa-solid fa-video text-[#1877F2] mr-3 text-lg"></i> ${q.resolution}</span> 
                            <span class="bg-green-100 text-green-700 border border-green-200 text-xs sm:text-sm px-3 sm:px-4 py-2 rounded-md font-bold transition-all duration-300 hover:bg-green-600 hover:text-white flex items-center gap-2 shadow-sm">
                                <i class="fa-solid fa-download transition-transform duration-300"></i> Download
                            </span>`;
                        
                        btn.onclick = () => handleDownloadClick(q.height);
                        resList.appendChild(btn);
                    });
                    
                    document.getElementById('resultSection').classList.remove('hidden');
                } else {
                    showCustomAlert(data.error || 'An error occurred while fetching video info.');
                }
            } catch (err) {
                document.getElementById('loading').classList.add('hidden');
                showCustomAlert('Server connection failed. Is the Python backend running?');
            }
        }

        let selectedHeight = '';
        
        // ── Robust Download Handler (fetch + Blob with error catching) ──
        async function handleDownloadClick(height) {
            selectedHeight = height;
            
            let vidTitle = document.getElementById('videoTitle').innerText || 'Video';
            const downloadUrl = `/api/download?url=${encodeURIComponent(currentVideoUrl)}&res=${selectedHeight}&title=${encodeURIComponent(vidTitle)}`;
            
            // Show processing state
            showCustomAlert('Processing your download... Please wait.', 'Downloading', 'fa-solid fa-spinner fa-spin');

            try {
                const response = await fetch(downloadUrl);
                const contentType = response.headers.get('Content-Type') || '';

                if (response.ok && (contentType.includes('video') || contentType.includes('octet-stream'))) {
                    // Success — create blob download
                    const blob = await response.blob();
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `${vidTitle}.mp4`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                    closeCustomAlert();
                } else {
                    // Error response — parse JSON and show error in modal
                    try {
                        const data = await response.json();
                        showCustomAlert(data.error || 'Download failed. Please try again.');
                    } catch (e) {
                        showCustomAlert('Download failed. The server returned an unexpected response.');
                    }
                }
            } catch (err) {
                showCustomAlert('Download failed. Please check your connection and try again.');
            }
        }


    // ── Google Translate Helper ──
    let _langRetries = 0;
    const MAX_LANG_RETRIES = 10;

    function changeLanguage(langCode) {
        var selectField = document.querySelector("select.goog-te-combo");
        if(selectField) {
            selectField.value = langCode;
            selectField.dispatchEvent(new Event('change'));
            _langRetries = 0;
        } else if (_langRetries < MAX_LANG_RETRIES) {
            _langRetries++;
            setTimeout(function() { changeLanguage(langCode); }, 500);
        }
    }

    function translateToBangla() {
        var selector = document.getElementById('global-lang-selector');
        if (selector) selector.value = 'bn';
        changeLanguage('bn');
    }
