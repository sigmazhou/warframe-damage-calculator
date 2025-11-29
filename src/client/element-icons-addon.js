// Element icon configuration
const ELEMENT_ICONS = {
    'impact': 'https://wiki.warframe.com/images/DmgImpactSmall64.png',
    'puncture': 'https://wiki.warframe.com/images/DmgPunctureSmall64.png',
    'slash': 'https://wiki.warframe.com/images/DmgSlashSmall64.png',
    'cold': 'https://wiki.warframe.com/images/DmgColdSmall64.png',
    'electricity': 'https://wiki.warframe.com/images/DmgElectricitySmall64.png',
    'heat': 'https://wiki.warframe.com/images/DmgHeatSmall64.png',
    'toxin': 'https://wiki.warframe.com/images/DmgToxinSmall64.png',
    'blast': 'https://wiki.warframe.com/images/DmgBlastSmall64.png',
    'corrosive': 'https://wiki.warframe.com/images/DmgCorrosiveSmall64.png',
    'gas': 'https://wiki.warframe.com/images/DmgGasSmall64.png',
    'magnetic': 'https://wiki.warframe.com/images/DmgMagneticSmall64.png',
    'radiation': 'https://wiki.warframe.com/images/DmgRadiationSmall64.png',
    'viral': 'https://wiki.warframe.com/images/DmgViralSmall64.png',
    'void': 'https://wiki.warframe.com/images/DmgVoidSmall64.png',
    'tau': 'https://wiki.warframe.com/images/DmgTauSmall64.png',
    'true_dmg': 'https://wiki.warframe.com/images/DmgTrueSmall64.png'
};

// Function to enhance select element with custom dropdown
function enhanceElementDropdown(originalSelect) {
    // Check if already enhanced
    if (originalSelect.dataset.enhanced === 'true') return;
    originalSelect.dataset.enhanced = 'true';

    // Get the original styles
    const computedStyle = window.getComputedStyle(originalSelect);
    const originalWidth = originalSelect.offsetWidth || computedStyle.width;

    // Hide original select
    originalSelect.style.display = 'none';

    // Create wrapper to maintain layout
    const wrapper = document.createElement('div');
    wrapper.style.cssText = `
        display: inline-block;
        width: ${originalWidth}px;
        position: relative;
    `;

    // Create custom dropdown container
    const customDropdown = document.createElement('div');
    customDropdown.className = 'custom-element-dropdown';
    customDropdown.style.cssText = 'position: relative; width: 100%;';

    // Create button to show selected value
    const button = document.createElement('button');
    button.type = 'button';
    button.style.cssText = `
        width: 100%;
        text-align: left;
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 4px 8px;
        border: 1px solid #444;
        border-radius: 3px;
        background: #2a2a2a;
        color: #e0e0e0;
        cursor: pointer;
        font-size: 13px;
        min-height: 28px;
    `;

    // Create dropdown menu
    const menu = document.createElement('div');
    menu.className = 'dropdown-menu';
    menu.style.cssText = `
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: #2a2a2a;
        border: 1px solid #444;
        border-radius: 3px;
        max-height: 300px;
        overflow-y: auto;
        z-index: 10000;
        display: none;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        margin-top: 2px;
    `;

    // Function to populate menu
    function populateMenu() {
        menu.innerHTML = '';

        Array.from(originalSelect.options).forEach((option, index) => {
            const item = document.createElement('div');
            item.className = 'dropdown-item';
            item.style.cssText = `
                padding: 6px 8px;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 6px;
                color: #e0e0e0;
                font-size: 13px;
            `;

            // Add icon if element has one
            const icon = ELEMENT_ICONS[option.value];
            if (icon && option.value) {
                const img = document.createElement('img');
                img.src = icon;
                img.alt = option.textContent;
                img.style.cssText = 'width: 18px; height: 18px; object-fit: contain; flex-shrink: 0;';
                img.onerror = function() { this.style.display = 'none'; };
                item.appendChild(img);
            } else if (option.value) {
                // Add spacer for items without icons to keep alignment
                const spacer = document.createElement('div');
                spacer.style.cssText = 'width: 18px; height: 18px; flex-shrink: 0;';
                item.appendChild(spacer);
            }

            const text = document.createElement('span');
            text.textContent = option.textContent;
            text.style.cssText = 'flex: 1;';
            item.appendChild(text);

            // Handle hover
            item.addEventListener('mouseenter', () => {
                item.style.backgroundColor = '#3a3a3a';
            });
            item.addEventListener('mouseleave', () => {
                item.style.backgroundColor = '';
            });

            // Handle click
            item.addEventListener('click', () => {
                originalSelect.selectedIndex = index;
                updateButton();
                menu.style.display = 'none';

                // Trigger change event on original select
                const event = new Event('change', { bubbles: true });
                originalSelect.dispatchEvent(event);
            });

            menu.appendChild(item);
        });
    }

    // Update button display
    function updateButton() {
        const selected = originalSelect.options[originalSelect.selectedIndex];
        button.innerHTML = '';

        if (selected && selected.value) {
            const icon = ELEMENT_ICONS[selected.value];
            if (icon) {
                const img = document.createElement('img');
                img.src = icon;
                img.alt = selected.textContent;
                img.style.cssText = 'width: 18px; height: 18px; object-fit: contain; flex-shrink: 0;';
                img.onerror = function() { this.style.display = 'none'; };
                button.appendChild(img);
            }
        }

        const text = document.createElement('span');
        text.textContent = selected ? selected.textContent : 'Select...';
        text.style.cssText = 'flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;';
        button.appendChild(text);

        // Add arrow indicator
        const arrow = document.createElement('span');
        arrow.textContent = '▼';
        arrow.style.cssText = 'font-size: 8px; opacity: 0.7; flex-shrink: 0;';
        button.appendChild(arrow);
    }

    // Toggle menu
    button.addEventListener('click', (e) => {
        e.stopPropagation();
        e.preventDefault();
        const isOpen = menu.style.display === 'block';

        // Close all other dropdowns
        document.querySelectorAll('.dropdown-menu').forEach(m => {
            if (m !== menu) m.style.display = 'none';
        });

        menu.style.display = isOpen ? 'none' : 'block';

        // Populate menu when opening (in case options changed)
        if (!isOpen) {
            populateMenu();
        }
    });

    // Close menu when clicking outside
    const closeHandler = (e) => {
        if (!wrapper.contains(e.target)) {
            menu.style.display = 'none';
        }
    };
    document.addEventListener('click', closeHandler);

    // Assemble custom dropdown
    customDropdown.appendChild(button);
    customDropdown.appendChild(menu);
    wrapper.appendChild(customDropdown);

    // Insert wrapper after original select
    originalSelect.parentNode.insertBefore(wrapper, originalSelect.nextSibling);

    // Initialize
    populateMenu();
    updateButton();

    // Listen for programmatic changes to original select
    const observer = new MutationObserver(() => {
        populateMenu();
        updateButton();
    });

    observer.observe(originalSelect, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['value']
    });

    originalSelect.addEventListener('change', updateButton);
}

// Function to enhance all element dropdowns
function enhanceAllElementDropdowns() {
    const selects = document.querySelectorAll('.element-select');
    console.log('Found element selects:', selects.length);
    selects.forEach(select => {
        // Wait for options to be populated
        const checkAndEnhance = () => {
            if (select.options.length > 1) { // More than just the placeholder
                console.log('Enhancing select with', select.options.length, 'options');
                enhanceElementDropdown(select);
            } else {
                // Try again in a bit
                setTimeout(checkAndEnhance, 50);
            }
        };
        checkAndEnhance();
    });
}

// Initialize
function init() {
    console.log('Initializing element icon addon');
    enhanceAllElementDropdowns();
}

// Wait for both DOM and script.js to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(init, 200);
    });
} else {
    setTimeout(init, 200);
}

// Watch for new builds being added
const buildsObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
            if (node.nodeType === 1 && (node.classList.contains('build') || node.querySelector)) {
                const selects = node.querySelectorAll ? node.querySelectorAll('.element-select') : [];
                selects.forEach(select => {
                    if (select.dataset.enhanced !== 'true') {
                        setTimeout(() => {
                            if (select.options.length > 1) {
                                enhanceElementDropdown(select);
                            }
                        }, 200);
                    }
                });
            }
        });
    });
});

// Start observing when ready
setTimeout(() => {
    const buildsContainer = document.getElementById('builds-container');
    if (buildsContainer) {
        buildsObserver.observe(buildsContainer, {
            childList: true,
            subtree: true
        });
    }
}, 300);