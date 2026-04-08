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
                alert('Browser blocked clipboard access! Please manually paste the link.');
            }
        }

        let currentVideoUrl = "";

        async function fetchVideoInfo() {
            currentVideoUrl = document.getElementById('videoUrl').value.trim();
            if(!currentVideoUrl) {
                alert('Please enter a Facebook video URL!');
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
                    document.getElementById('videoThumb').src = data.thumbnail;
                    document.getElementById('videoTitle').innerText = data.title;
                    
                    const resList = document.getElementById('resolutionsList');
                    resList.innerHTML = ''; 
                    
                    const fixedQualities = [
                        { label: '4K (Ultra HD)', height: 2160 },
                        { label: '1080p (HD)', height: 1080 },
                        { label: '720p (SD)', height: 720 },
                        { label: '420p (Basic)', height: 420 }
                    ];

                    fixedQualities.forEach(q => {
                        const btn = document.createElement('button');
                        btn.className = 'w-full flex justify-between items-center px-4 py-3 border border-gray-200 rounded-lg bg-white hover:bg-blue-50 transition-all duration-300 font-medium text-gray-800 shadow-sm hover:shadow-md transform hover:-translate-y-1 hover-bounce text-sm sm:text-base';
                        
                        btn.innerHTML = `
                            <span class="flex items-center"><i class="fa-solid fa-video text-[#1877F2] mr-3 text-lg"></i> ${q.label}</span> 
                            <span class="bg-green-100 text-green-700 border border-green-200 text-xs sm:text-sm px-3 sm:px-4 py-2 rounded-md font-bold transition-all duration-300 hover:bg-green-600 hover:text-white flex items-center gap-2 shadow-sm">
                                <i class="fa-solid fa-download transition-transform duration-300"></i> Download
                            </span>`;
                        
                        btn.onclick = () => handleDownloadClick(q.height);
                        resList.appendChild(btn);
                    });
                    
                    document.getElementById('resultSection').classList.remove('hidden');
                } else {
                    alert(data.error || 'An error occurred while fetching video info.');
                }
            } catch (err) {
                document.getElementById('loading').classList.add('hidden');
                alert('Server connection failed. Is the Python backend running?');
            }
        }

        let selectedHeight = '';
        
        function handleDownloadClick(height) {
            selectedHeight = height;
            
            const modal = document.getElementById('videoAdModal');
            modal.classList.remove('hidden');
            
            let timeLeft = 5;
            document.getElementById('timeCount').innerText = timeLeft;
            
            const timer = setInterval(() => {
                timeLeft--;
                document.getElementById('timeCount').innerText = timeLeft;
                
                if(timeLeft <= 0) {
                    clearInterval(timer);
                    modal.classList.add('hidden');
                    
                    const downloadUrl = `/api/download?url=${encodeURIComponent(currentVideoUrl)}&res=${selectedHeight}`;
                    window.location.href = downloadUrl;
                }
            }, 1000);
        }


    function changeLanguage(langCode) {
        var selectField = document.querySelector("select.goog-te-combo");
        if(selectField) {
            selectField.value = langCode;
            selectField.dispatchEvent(new Event('change'));
        } else {
            setTimeout(function() { changeLanguage(langCode); }, 500);
        }
    }

    function translateToBangla() {
        var selector = document.getElementById('global-lang-selector');
        selector.value = 'bn';
        changeLanguage('bn');
    }

