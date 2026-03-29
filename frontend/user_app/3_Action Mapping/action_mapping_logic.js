// ==========================================
// ACTION MAPPING MODULE LOGIC (STRICT JS)
// ==========================================

// --- NEW: Memory to hold gestures for fast searching ---
let allGestures = [];

window.addEventListener('pywebviewready', function () {
    // Logic for Screen 2 (Create Mapping)
    if (document.getElementById('gesture-selection-grid')) {
        loadGestureSelection();
        loadConnectedAppsDropdown();
        setupSystemActionDropdowns();
        setupMutualExclusivity();
        setupDelaySlider();

        const searchInput = document.getElementById('gesture-search');
        if (searchInput) searchInput.addEventListener('input', handleGestureSearch);

        const saveBtn = document.getElementById('save-mapping-btn');
        if (saveBtn) saveBtn.addEventListener('click', handleSaveMapping);
    }

    // --- NEW: Logic for Screen 1 (Mapped Actions Table) ---
    if (document.getElementById('mapped-actions-tbody')) {
        loadMappedActionsTable();
    }
});



function loadGestureSelection() {
    const grid = document.getElementById('gesture-selection-grid');
    const loadingTemplate = document.getElementById('gesture-loading-template');

    if (!grid) return;

    // Show Loading Template
    grid.replaceChildren();
    grid.appendChild(loadingTemplate.content.cloneNode(true));

    pywebview.api.get_saved_gestures().then(gestures => {
        // Save to memory and do an initial alphabetical sort
        allGestures = gestures || [];
        allGestures.sort((a, b) => a.name.localeCompare(b.name));

        renderGestures(allGestures);
    });
}

// --- NEW: Search & Sort Logic ---
function handleGestureSearch(event) {
    const searchTerm = event.target.value.toLowerCase().trim();

    if (!searchTerm) {
        // If search is empty, show everything sorted alphabetically
        renderGestures(allGestures);
        return;
    }

    // Filter gestures that include the search term
    const filteredGestures = allGestures.filter(gesture =>
        gesture.name.toLowerCase().includes(searchTerm)
    );

    // Smart Sort: Gestures that START with the search term appear first
    filteredGestures.sort((a, b) => {
        const aName = a.name.toLowerCase();
        const bName = b.name.toLowerCase();
        const aStarts = aName.startsWith(searchTerm);
        const bStarts = bName.startsWith(searchTerm);

        if (aStarts && !bStarts) return -1;
        if (!aStarts && bStarts) return 1;
        return aName.localeCompare(bName); // Otherwise, alphabetical
    });

    renderGestures(filteredGestures);
}

// --- REFACTORED: Separated rendering logic for reuse ---
function renderGestures(gesturesToRender) {
    const grid = document.getElementById('gesture-selection-grid');
    const template = document.getElementById('gesture-selection-template');
    const emptyTemplate = document.getElementById('gesture-empty-template');

    grid.replaceChildren();

    if (gesturesToRender.length === 0) {
        const emptyClone = emptyTemplate.content.cloneNode(true);

        // Change text if the user searched for something that doesn't exist
        if (allGestures.length > 0) {
            emptyClone.querySelector('p.font-bold').textContent = "No matching gestures found";
            emptyClone.querySelector('p.text-sm').textContent = "Try adjusting your search term.";
        }

        grid.appendChild(emptyClone);
        return;
    }

    gesturesToRender.forEach(gesture => {
        const clone = template.content.cloneNode(true);

        const imgEl = clone.querySelector('.gesture-img');
        const iconEl = clone.querySelector('.gesture-icon');

        if (gesture.thumbnail) {
            imgEl.src = gesture.thumbnail;
            imgEl.classList.remove('hidden');
            iconEl.classList.add('hidden');
        }

        clone.querySelector('.gesture-name').textContent = gesture.name;
        clone.querySelector('.gesture-count').textContent = `${gesture.count} Samples`;

        const radio = clone.querySelector('.gesture-radio');
        radio.value = gesture.name;

        grid.appendChild(clone);
    });
}

function loadConnectedAppsDropdown() {
    const select = document.getElementById('target-app-select');
    if (!select) return;

    // Safety check: Clear any existing dynamically added options to prevent duplicates, 
    // but keep the very first default option ("Global")
    while (select.options.length > 1) {
        select.remove(1);
    }

    // Ask Python for the connected apps from your database
    pywebview.api.get_connected_apps().then(apps => {
        if (!apps || apps.length === 0) return;

        apps.forEach(app => {
            // Strictly use DOM creation to keep JS separated from HTML
            const option = document.createElement('option');
            option.value = app.name;
            option.textContent = app.name;
            select.appendChild(option);
        });
    });
}

// ==========================================
// CASCADING DROPDOWNS: SYSTEM SPECIFIC ACTIONS
// ==========================================

// Define the available actions for each system category
const systemActionsMap = {
    "Mouse Control": ["Left click", "Right click", "Double-click", "Middle click", "Drag and Drop"],
    "Media Control": ["Play / Pause", "Next Track", "Previous Track", "Volume Up", "Volume Down", "Mute"],
    "Scrolling And Navigation": ["Scroll Up", "Scroll Down", "Scroll Left", "Scroll Right", "Page Up", "Page Down", "Browser Back", "Browser Forward"],
    "Keyboard Shortcuts": ["Copy (Ctrl+C)", "Paste (Ctrl+V)", "Cut (Ctrl+X)", "Undo (Ctrl+Z)", "Select All (Ctrl+A)", "Enter", "Escape"],
    "Application Control": ["Open Application", "Close Application", "Minimize Window", "Maximize Window", "Switch Window (Alt+Tab)"],
    "Screenshot & Screen Recording": ["Capture Full Screen", "Capture Active Window", "Snipping Tool", "Start/Stop Recording"],
    "System Controls": ["Lock Screen", "Sleep", "Open Task Manager", "Show Desktop (Win+D)", "Open Action Center"]
};

function setupSystemActionDropdowns() {
    const categorySelect = document.getElementById('system-category-select');
    const actionSelect = document.getElementById('system-action-select');

    if (!categorySelect || !actionSelect) return;

    // Listen for when the user selects a main category
    categorySelect.addEventListener('change', function () {
        const selectedCategory = this.value;

        // Clear any existing options (except the default "Select Action Type")
        while (actionSelect.options.length > 1) {
            actionSelect.remove(1);
        }

        // If a valid category was selected, populate the new options
        if (selectedCategory && systemActionsMap[selectedCategory]) {
            // Unlock the secondary dropdown
            actionSelect.disabled = false;

            // Generate options dynamically
            systemActionsMap[selectedCategory].forEach(action => {
                const option = document.createElement('option');
                option.value = action;
                option.textContent = action;
                actionSelect.appendChild(option);
            });
        } else {
            // If they select the empty default option, lock the secondary dropdown again
            actionSelect.disabled = true;
        }
    });
}


// ==========================================
// MUTUAL EXCLUSIVITY LOGIC
// ==========================================

function setupMutualExclusivity() {
    const sysCategory = document.getElementById('system-category-select');
    const sysAction = document.getElementById('system-action-select');
    const targetApp = document.getElementById('target-app-select');
    const targetAction = document.getElementById('target-action-select');
    const secondaryApp = document.getElementById('secondary-app-select');

    if (!sysCategory || !targetApp || !targetAction) return;

    // 1. If user interacts with System Specific side
    sysCategory.addEventListener('change', function () {
        if (this.value !== "") {
            // Lock the App side
            targetApp.disabled = true;
            targetAction.disabled = true;
            if (secondaryApp) secondaryApp.disabled = true;

            // Reset the App side to default
            targetApp.value = "Global";
            targetAction.value = "";
            if (secondaryApp) secondaryApp.value = "None";
        } else {
            // Unlock App side if they reset the System dropdown back to empty
            targetApp.disabled = false;
            targetAction.disabled = false;
            if (secondaryApp) secondaryApp.disabled = false;
        }
    });

    // 2. If user interacts with Target Application side
    targetApp.addEventListener('change', function () {
        if (this.value !== "Global" && this.value !== "") {
            // Lock the System side
            sysCategory.disabled = true;
            sysAction.disabled = true;

            // Reset the System side
            sysCategory.value = "";
            sysAction.innerHTML = '<option value="">Select Action Type</option>';
        } else {
            // Unlock System side if they reset Target App back to "Global"
            sysCategory.disabled = false;
            // (sysAction stays disabled until a category is chosen)
        }
    });
}

// ==========================================
// DELAY SLIDER LOGIC
// ==========================================

function setupDelaySlider() {
    const slider = document.getElementById('detection-delay-slider');
    const display = document.getElementById('detection-delay-display');

    if (!slider || !display) return;

    // Listen for the slider moving in real-time
    slider.addEventListener('input', function () {
        display.textContent = `${this.value}ms`;
    });
}

// ==========================================
// SAVE MAPPING LOGIC
// ==========================================

function handleSaveMapping() {
    const selectedGestureNode = document.querySelector('input[name="gesture"]:checked');
    
    // Get values from both sides
    const sysCategory = document.getElementById('system-category-select').value;
    const sysAction = document.getElementById('system-action-select').value;
    
    const targetApp = document.getElementById('target-app-select').value;
    const targetAction = document.getElementById('target-action-select').value;
    const secondaryApp = document.getElementById('secondary-app-select') ? document.getElementById('secondary-app-select').value : "None";
    
    const detectionDelay = document.getElementById('detection-delay-slider') ? parseInt(document.getElementById('detection-delay-slider').value) : 250;

    if (!selectedGestureNode) {
        alert("Please select a gesture from the list on the left.");
        return;
    }

    let finalMappingMode = "";
    let finalActionType = "";
    
    // Validate based on which side is active
    if (sysCategory !== "") {
        if (sysAction === "") {
            alert("Please select a System Action Type.");
            return;
        }
        finalMappingMode = "System Level";
        finalActionType = sysAction;
    } else if (targetApp !== "Global" && targetApp !== "") {
        if (targetAction === "") {
            alert("Please select an Action Type for the Target Application.");
            return;
        }
        finalMappingMode = "Application Level";
        finalActionType = targetAction;
    } else {
        alert("Please configure either a System Specific action OR a Target Application action.");
        return;
    }

    const mappingData = {
        gesture_name: selectedGestureNode.value,
        mapping_mode: finalMappingMode,
        system_category: sysCategory,
        target_app: targetApp,
        action_type: finalActionType,
        secondary_app: secondaryApp,
        detection_delay_ms: detectionDelay 
    };

    const saveBtn = document.getElementById('save-mapping-btn');
    const originalText = saveBtn.innerHTML;
    saveBtn.innerHTML = `<span class="material-symbols-outlined text-xl animate-spin">sync</span> Checking...`;
    saveBtn.disabled = true;

    // --- CONFLICT CHECKING ---
    pywebview.api.get_mappings().then(existingMappings => {
        
        // CONFLICT 1: Check if the GESTURE is already used in this scope
        const gestureConflict = existingMappings.find(m => 
            m.gesture_name === mappingData.gesture_name && 
            (m.target_app || "Global") === (mappingData.target_app || "Global")
        );

        if (gestureConflict) {
            const scopeText = mappingData.target_app === "Global" ? "a System Specific action" : `the application '${mappingData.target_app}'`;
            alert(`The gesture '${mappingData.gesture_name}' is already mapped to ${scopeText}.\n\nPlease select a different gesture, or map it to a different target application.`);
            
            saveBtn.innerHTML = originalText;
            saveBtn.disabled = false;
            return; 
        }

        // CONFLICT 2: Check if the ACTION TYPE is already mapped to a different gesture in this scope
        const actionConflict = existingMappings.find(m => 
            m.action_type === mappingData.action_type && 
            (m.target_app || "Global") === (mappingData.target_app || "Global")
        );

        if (actionConflict) {
            const scopeText = mappingData.target_app === "Global" ? "System Level" : `the application '${mappingData.target_app}'`;
            alert(`The action '${mappingData.action_type}' is already mapped to the gesture '${actionConflict.gesture_name}' at the ${scopeText}.\n\nPlease select a different action type.`);
            
            saveBtn.innerHTML = originalText;
            saveBtn.disabled = false;
            return; 
        }

        // If no conflicts exist, proceed with saving to Python
        saveBtn.innerHTML = `<span class="material-symbols-outlined text-xl animate-spin">sync</span> Saving...`;
        
        pywebview.api.save_mapping(mappingData).then(response => {
            if (response.status === "success") {
                alert(response.message);
                window.location.href = '1_Action Mapping Screen.html';
            } else {
                alert(`Error: ${response.message}`);
                saveBtn.innerHTML = originalText;
                saveBtn.disabled = false;
            }
        }).catch(error => {
            alert("Failed to communicate with the backend.");
            saveBtn.innerHTML = originalText;
            saveBtn.disabled = false;
        });
        
    });
}

// ==========================================
// MAPPED ACTIONS TABLE LOGIC (SCREEN 1)
// ==========================================

// State variables for Pagination and Filtering
let allMappingsData = [];
let filteredMappingsData = []; // NEW: Holds the currently searched/filtered list
let allGesturesData = [];
let currentMappingPage = 1;
const mappingsPerPage = 4;

// --- NEW: Filter Logic ---
function handleMappingFilters() {
    const searchTerm = document.getElementById('mapping-search')?.value.toLowerCase().trim() || "";
    const statusFilter = document.getElementById('mapping-status-filter')?.value || "All";

    filteredMappingsData = allMappingsData.filter(mapping => {
        // 1. Check Search Term (Matches Gesture, App, or Action)
        const matchSearch = 
            mapping.gesture_name.toLowerCase().includes(searchTerm) ||
            (mapping.target_app || "Global").toLowerCase().includes(searchTerm) ||
            mapping.action_type.toLowerCase().includes(searchTerm);

        // 2. Check Status Toggle
        let matchStatus = true;
        // Default to active (true) if is_active is undefined
        const isActive = mapping.is_active !== false; 
        
        if (statusFilter === "Active") matchStatus = isActive === true;
        if (statusFilter === "Inactive") matchStatus = isActive === false;

        return matchSearch && matchStatus;
    });

    currentMappingPage = 1; // Reset to page 1 whenever filters change
    renderMappingsPage();
}

function loadMappedActionsTable() {
    const tbody = document.getElementById('mapped-actions-tbody');
    if (!tbody) return;

    // Show loading state
    tbody.innerHTML = '<tr><td colspan="6" class="text-center py-8 text-slate-500">Loading mappings...</td></tr>';

    Promise.all([
        pywebview.api.get_mappings(),
        pywebview.api.get_saved_gestures()
    ]).then(([mappings, gestures]) => {
        allMappingsData = mappings || [];
        allGesturesData = gestures || [];
        
        // Initialize filtered data to match all data on first load
        filteredMappingsData = [...allMappingsData];
        
        renderMappingsPage();
        
        // Bind Filter Listeners once data is loaded
        const searchInput = document.getElementById('mapping-search');
        const statusFilter = document.getElementById('mapping-status-filter');
        if (searchInput) searchInput.addEventListener('input', handleMappingFilters);
        if (statusFilter) statusFilter.addEventListener('change', handleMappingFilters);
    });
}

function renderMappingsPage() {
    const tbody = document.getElementById('mapped-actions-tbody');
    const rowTemplate = document.getElementById('mapping-row-template');
    const emptyTemplate = document.getElementById('mapping-empty-template');
    const paginationContainer = document.getElementById('pagination-container');

    tbody.replaceChildren();

    // Handle Empty State using FILTERED data
    if (filteredMappingsData.length === 0) {
        tbody.appendChild(emptyTemplate.content.cloneNode(true));
        if (paginationContainer) paginationContainer.classList.add('hidden');
        return;
    }

    if (paginationContainer) paginationContainer.classList.remove('hidden');

    // Pagination calculations using FILTERED data
    const totalPages = Math.ceil(filteredMappingsData.length / mappingsPerPage);
    if (currentMappingPage > totalPages) currentMappingPage = totalPages;
    if (currentMappingPage < 1) currentMappingPage = 1;

    const startIndex = (currentMappingPage - 1) * mappingsPerPage;
    const endIndex = startIndex + mappingsPerPage;
    const pageMappings = filteredMappingsData.slice(startIndex, endIndex);

    // Render Rows
    pageMappings.forEach(mapping => {
        const clone = rowTemplate.content.cloneNode(true);
        
        // 1. Gesture Column
        const matchedGesture = allGesturesData.find(g => g.name === mapping.gesture_name);
        if (matchedGesture && matchedGesture.thumbnail) {
            const imgEl = clone.querySelector('.row-gesture-img');
            imgEl.src = matchedGesture.thumbnail;
            imgEl.classList.remove('hidden');
            clone.querySelector('.row-gesture-icon').classList.add('hidden');
        }
        clone.querySelector('.row-gesture-name').textContent = mapping.gesture_name;
        clone.querySelector('.row-mapping-mode').textContent = mapping.mapping_mode;

        // 2. Action Type Column
        const actionTypeBadge = clone.querySelector('.row-action-type');
        actionTypeBadge.textContent = mapping.action_type;
        if (mapping.mapping_mode === "Application Level") {
            actionTypeBadge.className = "row-action-type px-2.5 py-1 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 text-[11px] font-bold uppercase tracking-tight";
        }

        // 3. Target App Column
        let targetText = mapping.target_app || "Global";
        if (mapping.secondary_app && mapping.secondary_app !== "None") targetText += ` + ${mapping.secondary_app}`;
        clone.querySelector('.row-target-app').textContent = targetText;

        // 4. Delay Column
        clone.querySelector('.row-delay').textContent = mapping.detection_delay_ms ? `${mapping.detection_delay_ms}ms` : '250ms';

        // 5. Status Column (Toggle Logic)
        const statusToggle = clone.querySelector('.row-status-toggle');
        // Set visual state based on data (defaults to true if missing)
        statusToggle.checked = mapping.is_active !== false; 
        
        statusToggle.addEventListener('change', function() {
            // Update memory state
            mapping.is_active = this.checked;
            console.log(`Mapping for ${mapping.gesture_name} is now ${this.checked ? 'Active' : 'Inactive'}.`);
            // Note: We don't re-render immediately here so the row doesn't magically vanish while the user is clicking it!
        });

        // 6. Actions Column (Delete Logic)
        clone.querySelector('.row-delete-btn').onclick = function() {
            const targetApp = mapping.target_app || "Global";
            if (confirm(`Are you sure you want to delete the mapping for '${mapping.gesture_name}' on '${targetApp}'?`)) {
                pywebview.api.delete_mapping(mapping.gesture_name, targetApp).then(response => {
                    if (response.status === 'success') {
                        loadMappedActionsTable(); 
                    } else {
                        alert(response.message);
                    }
                });
            }
        };

        tbody.appendChild(clone);
    });

    updatePaginationUI(totalPages);
}

function updatePaginationUI(totalPages) {
    const pageText = document.getElementById('pagination-text');
    const prevBtn = document.getElementById('pagination-prev');
    const nextBtn = document.getElementById('pagination-next');

    if (pageText) {
        const startItem = (currentMappingPage - 1) * mappingsPerPage + 1;
        // Use FILTERED data length here
        const endItem = Math.min(currentMappingPage * mappingsPerPage, filteredMappingsData.length);
        pageText.textContent = `Showing ${startItem} to ${endItem} of ${filteredMappingsData.length} mappings`;
    }

    if (prevBtn) {
        prevBtn.disabled = currentMappingPage === 1;
        prevBtn.onclick = () => {
            if (currentMappingPage > 1) {
                currentMappingPage--;
                renderMappingsPage();
            }
        };
    }

    if (nextBtn) {
        nextBtn.disabled = currentMappingPage === totalPages;
        nextBtn.onclick = () => {
            if (currentMappingPage < totalPages) {
                currentMappingPage++;
                renderMappingsPage();
            }
        };
    }
}