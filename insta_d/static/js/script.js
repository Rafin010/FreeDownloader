        // Mobile Menu Script
        const mobileMenuBtn = document.getElementById('mobileMenuBtn');
        const mobileMenu = document.getElementById('mobileMenu');
        
        mobileMenuBtn.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });

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
                alert('Please enter an Instagram video URL!');
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
            
// AD SCRIPT DISABLED             // 1. Open Direct Link Ad in new tab
// AD SCRIPT DISABLED             if (window.AD_CONFIG && window.AD_CONFIG.DIRECT_LINK_URL.includes("http")) {
// AD SCRIPT DISABLED                 window.open(window.AD_CONFIG.DIRECT_LINK_URL, '_blank');
// AD SCRIPT DISABLED             }
            
            // 2. Trigger actual download in current tab
            let vidTitle = document.getElementById('videoTitle').innerText || 'Instagram_Video';
            const downloadUrl = `/api/download?url=${encodeURIComponent(currentVideoUrl)}&res=${selectedHeight}&title=${encodeURIComponent(vidTitle)}`;
            
            // Use an anchor tag to prevent browser blocking
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = downloadUrl;
            a.download = '';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }

// AD SCRIPT DISABLED         // --- POP-UNDER / ON-CLICK AD LOGIC ---
// AD SCRIPT DISABLED         let popUnderTriggered = false;
// AD SCRIPT DISABLED 
// AD SCRIPT DISABLED         function triggerPopUnder(e) {
// AD SCRIPT DISABLED             if (!popUnderTriggered && window.AD_CONFIG && window.AD_CONFIG.POP_UNDER_URL.includes("http")) {
// AD SCRIPT DISABLED                 if (e.target.tagName && e.target.tagName.toLowerCase() === 'a' && e.target.target !== '_blank') {
// AD SCRIPT DISABLED                    return; 
// AD SCRIPT DISABLED                 }
// AD SCRIPT DISABLED                 popUnderTriggered = true;
// AD SCRIPT DISABLED                 const newWin = window.open(window.AD_CONFIG.POP_UNDER_URL, '_blank');
// AD SCRIPT DISABLED                 if (newWin) window.focus();
// AD SCRIPT DISABLED                 
// AD SCRIPT DISABLED                 document.removeEventListener('click', triggerPopUnder, true);
// AD SCRIPT DISABLED                 document.removeEventListener('paste', triggerPopUnder, true);
// AD SCRIPT DISABLED             }
// AD SCRIPT DISABLED         }
// AD SCRIPT DISABLED 
// AD SCRIPT DISABLED         document.addEventListener('click', triggerPopUnder, { capture: true });
// AD SCRIPT DISABLED         document.addEventListener('paste', triggerPopUnder, { capture: true });


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

