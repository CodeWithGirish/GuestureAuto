// ==========================================
// INITIALIZATION
// ==========================================
window.addEventListener('pywebviewready', function () {
    console.log("Dashboard API Bridge Ready");

    // Call the new metrics function when Python is ready
    loadDashboardMetrics();
});

// ==========================================
// SYSTEM CONTROL & PREVIEW
// ==========================================
let isSystemActive = false;

// --- Helper Function to fix ReferenceError ---
function updateSystemUI(active) {
    const statusText = document.getElementById('system-status-text');
    const statusDot = document.getElementById('system-status-dot');
    const dashPlaceholder = document.getElementById('dashboard-placeholder');

    if (active) {
        if (statusText) {
            statusText.innerText = "Online";
            statusText.className = "text-[10px] font-bold uppercase tracking-wider text-emerald-500";
        }
        if (statusDot) {
            statusDot.className = "size-2 rounded-full bg-emerald-500 animate-pulse";
        }
        if (dashPlaceholder) dashPlaceholder.style.display = 'none';
    } else {
        if (statusText) {
            statusText.innerText = "Offline";
            statusText.className = "text-[10px] font-bold uppercase tracking-wider text-slate-500";
        }
        if (statusDot) {
            statusDot.className = "size-2 rounded-full bg-slate-400";
        }
        if (dashPlaceholder) dashPlaceholder.style.display = 'flex';

        // Clear feed on stop
        const dashFeed = document.getElementById('dashboard-live-feed');
        if (dashFeed) dashFeed.src = "";
    }
}

function startSystem() {
    pywebview.api.start_scan().then((response) => {
        if (response.status === "success") {
            isSystemActive = true; // System is now active
            updateSystemUI(true);  // Helper to change UI to 'Online'
        }
    });
}

function stopSystem() {
    pywebview.api.stop_scan().then((response) => {
        if (response.status === "success") {
            isSystemActive = false; // System is now inactive
            updateSystemUI(false); // Helper to change UI to 'Offline'
        }
    });
}

function toggleFloatWindow() {
    // Check if the system is started before allowing the window to open
    if (!isSystemActive) {
        alert("Please start the system first before opening the Floating Window.");
        return;
    }

    // Call the API only when the button is explicitly clicked
    pywebview.api.toggle_float_window().then(response => {
        console.log("Floating window request sent.");
    });
}

function updateFrame(base64Image) {
    const dashFeed = document.getElementById('dashboard-live-feed');
    if (dashFeed && isSystemActive) {
        dashFeed.src = base64Image;
    }
}

function safeNavigate(targetUrl) {
    // Ensure camera is stopped before switching pages to avoid thread errors
    pywebview.api.stop_scan().then(() => {
        window.location.href = targetUrl;
    });
}

// ==========================================
// METRICS & DATA FETCHING
// ==========================================
function loadDashboardMetrics() {
    const connectedAppsCountEl = document.getElementById('connected-apps-count');
    const activeGesturesCountEl = document.getElementById('active-gestures-count'); // New element

    // 1. Fetch the connected apps from the Integration API
    if (connectedAppsCountEl) {
        pywebview.api.get_connected_apps().then(apps => {
            const count = apps ? apps.length : 0;
            connectedAppsCountEl.innerText = count.toString().padStart(2, '0');
        });
    }

    // 2. Fetch the active gestures from the Action Mapping API
    if (activeGesturesCountEl) {
        pywebview.api.get_mappings().then(mappings => {
            if (!mappings) mappings = [];
            
            // Filter out any mappings that the user manually toggled off (Inactive)
            // If 'is_active' is undefined (older mappings), treat it as active (true)
            const activeMappings = mappings.filter(mapping => mapping.is_active !== false);
            
            const count = activeMappings.length;
            activeGesturesCountEl.innerText = count.toString().padStart(2, '0');
        });
    }
}