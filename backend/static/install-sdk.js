/**
 * Free Store Install Tracker SDK
 * Reports installation, uninstallation and heartbeats to track active users.
 */

(function() {
    const API_BASE = 'https://admin.freedownloader.top/api/install';
    // Fallback to localhost if testing locally
    const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    const API_URL = isLocal ? 'http://127.0.0.1:8000/api/install' : API_BASE;
    
    // Generate stable unique install ID if not exists
    let installId = localStorage.getItem('fs_install_id');
    let userId = localStorage.getItem('fs_popup_uid') || 'uid_' + Math.random().toString(36).substr(2, 9);
    
    if (!installId) {
        installId = 'inst_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('fs_install_id', installId);
        localStorage.setItem('fs_popup_uid', userId);
        
        // Register new install
        registerInstall();
    } else {
        // Send heartbeat
        sendHeartbeat();
    }

    const softwareName = window.FS_SOFTWARE_NAME || 'Unknown Web App';
    const appVersion = window.FS_APP_VERSION || '1.0.0';

    async function registerInstall() {
        try {
            await fetch(`${API_URL}/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    install_id: installId,
                    user_id: userId,
                    software_name: softwareName,
                    app_version: appVersion,
                    os_type: navigator.platform
                })
            });
        } catch (err) {}
    }

    async function sendHeartbeat() {
        try {
            await fetch(`${API_URL}/heartbeat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ install_id: installId })
            });
        } catch (err) {}
    }

    // Send heartbeat every 4 minutes (timeout is 15 minutes on server)
    setInterval(sendHeartbeat, 4 * 60 * 1000);

    // Provide hook for manual uninstall
    window.FS_Uninstall = async function() {
        try {
            await fetch(`${API_URL}/uninstall`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ install_id: installId })
            });
            localStorage.removeItem('fs_install_id');
        } catch (err) {}
    };

})();
