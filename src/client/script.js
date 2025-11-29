        document.addEventListener('DOMContentLoaded', function() {
            // Available elements from the Elements class
            const availableElements = [
                'impact', 'puncture', 'slash',
                'cold', 'electricity', 'heat', 'toxin',
                'blast', 'corrosive', 'gas', 'magnetic', 'radiation', 'viral',
                'void', 'tau', 'true_dmg'
            ];

            let availableBuffs = [];
            let buildIdCounter = 1;

            loadEnemyTypes();
            loadElementOptions();
            initializeDefaultElements();
            loadAvailableBuffs();

            // Initialize event listeners for the first build
            const firstBuild = document.querySelector('.build[data-build-id="1"]');
            setupBuildEventListeners(firstBuild);

            // Attach remove button listener for first build
            const firstRemoveBtn = firstBuild.querySelector('.remove-build-btn');
            if (firstRemoveBtn) {
                firstRemoveBtn.addEventListener('click', function() {
                    removeBuild(firstBuild);
                });
            }

            // Update remove button visibility initially
            updateRemoveButtons();

            function setupBuildEventListeners(build) {
                const buildId = build.getAttribute('data-build-id');
                const modSearch = build.querySelector('.mod-search-input');
                const searchResults = build.querySelector('.mod-search-results');
                const buffSearch = build.querySelector('.buff-search-input');
                const buffSearchResults = build.querySelector('.buff-search-results');
                const addElementBtn = build.querySelector('.add-element-btn');

                // === Setup search and add button listeners ===
                if (modSearch && searchResults) {
                    modSearch.addEventListener('input', function() {
                        const query = this.value.trim();
                        if (query.length < 1) {
                            searchResults.style.display = 'none';
                            return;
                        }

                        fetch(`/api/search-mods?q=${encodeURIComponent(query)}`)
                            .then(response => response.json())
                            .then(data => {
                                searchResults.innerHTML = '';
                                if (!data.success || data.mods.length === 0) {
                                    searchResults.innerHTML = '<div class="search-result-item">No mods found</div>';
                                } else {
                                    data.mods.forEach(mod => {
                                        const item = document.createElement('div');
                                        item.className = 'search-result-item';
                                        item.textContent = mod.name;
                                        item.setAttribute('data-mod-id', mod.id);
                                        item.addEventListener('click', function() {
                                            addModToBuild(build, mod.id, mod.name);
                                            modSearch.value = '';
                                            searchResults.style.display = 'none';
                                        });
                                        searchResults.appendChild(item);
                                    });
                                }
                                searchResults.style.display = 'block';
                            })
                            .catch(error => {
                                console.error('Search mods error:', error);
                                searchResults.innerHTML = '<div class="search-result-item">Search error</div>';
                                searchResults.style.display = 'block';
                            });
                    });
                }

                if (buffSearch && buffSearchResults) {
                    buffSearch.addEventListener('input', function() {
                        const query = this.value.trim().toLowerCase();
                        if (query.length < 1) {
                            buffSearchResults.style.display = 'none';
                            return;
                        }

                        const matchingBuffs = availableBuffs.filter(buff =>
                            buff.name.toLowerCase().includes(query)
                        );

                        buffSearchResults.innerHTML = '';
                        if (matchingBuffs.length === 0) {
                            buffSearchResults.innerHTML = '<div class="search-result-item">No buffs found</div>';
                        } else {
                            matchingBuffs.forEach(buff => {
                                const item = document.createElement('div');
                                item.className = 'search-result-item';
                                item.textContent = buff.name;
                                item.addEventListener('click', function() {
                                    addBuffToBuild(build, buff.name, buff.type);
                                    buffSearch.value = '';
                                    buffSearchResults.style.display = 'none';
                                });
                                buffSearchResults.appendChild(item);
                            });
                        }
                        buffSearchResults.style.display = 'block';
                    });
                }

                if (addElementBtn) {
                    addElementBtn.addEventListener('click', function() {
                        addWeaponElementForBuild(build);
                    });
                }

                // === Reattach listeners for cloned items (weapon elements, mods, buffs) ===
                // This handles both new builds and cloned builds with existing items

                // Reattach weapon element remove buttons
                const weaponElements = build.querySelector('.weapon-elements-container');
                build.querySelectorAll('.element-item').forEach(item => {
                    const removeBtn = item.querySelector('.remove-weapon-element-btn');
                    if (removeBtn) {
                        // Remove old listener by replacing the button
                        const newBtn = removeBtn.cloneNode(true);
                        removeBtn.parentNode.replaceChild(newBtn, removeBtn);
                        newBtn.addEventListener('click', function() {
                            weaponElements.removeChild(item);
                        });
                    }

                    // Reattach value input listener
                    const valueInput = item.querySelector('.element-value-input');
                    if (valueInput) {
                        valueInput.addEventListener('input', function() {
                            item.dataset.value = this.value;
                        });
                    }
                });

                // Reattach mod remove buttons
                const selectedMods = build.querySelector('.selected-mods-container');
                build.querySelectorAll('.mod-item:not(.buff-item)').forEach(item => {
                    const removeBtn = item.querySelector('.remove-mod-btn');
                    if (removeBtn) {
                        const newBtn = removeBtn.cloneNode(true);
                        removeBtn.parentNode.replaceChild(newBtn, removeBtn);
                        newBtn.addEventListener('click', function() {
                            selectedMods.removeChild(item);
                        });
                    }
                });

                // Reattach buff remove buttons
                const selectedBuffs = build.querySelector('.selected-buffs-container');
                build.querySelectorAll('.buff-item').forEach(item => {
                    const removeBtn = item.querySelector('.remove-buff-btn');
                    if (removeBtn) {
                        const newBtn = removeBtn.cloneNode(true);
                        removeBtn.parentNode.replaceChild(newBtn, removeBtn);
                        newBtn.addEventListener('click', function() {
                            selectedBuffs.removeChild(item);
                        });
                    }
                });
            }

            function loadEnemyTypes() {
                // Load enemy factions
                fetch('/api/enemy-factions')
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Populate all faction selects (for all builds)
                            const factionSelects = document.querySelectorAll('.enemy-faction-select');
                            factionSelects.forEach(factionSelect => {
                                factionSelect.innerHTML = '';
                                data.enemy_factions.forEach(faction => {
                                    const option = document.createElement('option');
                                    option.value = faction;
                                    option.textContent = faction.charAt(0).toUpperCase() + faction.slice(1);
                                    factionSelect.appendChild(option);
                                });
                            });
                        }
                    })
                    .catch(error => console.error('Load enemy factions failed:', error));

                // Load enemy types
                fetch('/api/enemy-types')
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Populate all type selects (for all builds)
                            const typeSelects = document.querySelectorAll('.enemy-type-select');
                            typeSelects.forEach(typeSelect => {
                                typeSelect.innerHTML = '';
                                data.enemy_types.forEach(type => {
                                    const option = document.createElement('option');
                                    option.value = type;
                                    option.textContent = type.charAt(0).toUpperCase() + type.slice(1);
                                    typeSelect.appendChild(option);
                                });
                            });
                        }
                    })
                    .catch(error => console.error('Load enemy types failed:', error));
            }

            function loadAvailableBuffs() {
                fetch('/api/ingame-buffs')
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Use buffs directly from API (already flattened)
                            availableBuffs = data.buffs;
                        }
                    })
                    .catch(error => console.error('Load available buffs failed:', error));
            }

            function loadElementOptions() {
                // Populate all element selects (for all builds)
                const elementSelects = document.querySelectorAll('.element-select');
                elementSelects.forEach(elementSelect => {
                    elementSelect.innerHTML = '<option value="">Add element...</option>';
                    availableElements.forEach(element => {
                        const option = document.createElement('option');
                        option.value = element;
                        option.textContent = element.charAt(0).toUpperCase() + element.slice(1).replace('_', ' ');
                        elementSelect.appendChild(option);
                    });
                });
            }

            function initializeDefaultElements() {
                // Add default 100 impact to first build
                const firstBuild = document.querySelector('.build[data-build-id="1"]');
                if (firstBuild) {
                    addWeaponElementForBuild(firstBuild, 'impact', 100);
                }
            }

            function addWeaponElementForBuild(build, elementName, value) {
                const weaponElements = build.querySelector('.weapon-elements-container');

                if (!weaponElements) return;

                // If elementName and value are not provided, get them from inputs
                if (elementName === undefined) {
                    const elementSelect = build.querySelector('.element-select');
                    const elementValue = build.querySelector('.element-value-input');
                    elementName = elementSelect.value;
                    value = parseFloat(elementValue.value);

                    if (!elementName || isNaN(value) || value <= 0) {
                        return;
                    }

                    // Reset inputs after adding
                    elementSelect.value = '';
                    elementValue.value = '';
                }

                // Check if element already exists
                const existingElements = weaponElements.querySelectorAll('.element-item');
                for (let item of existingElements) {
                    if (item.dataset.element === elementName) {
                        return; // Don't add duplicate
                    }
                }

                const elementItem = document.createElement('div');
                elementItem.className = 'element-item';
                elementItem.dataset.element = elementName;
                elementItem.dataset.value = value;
                elementItem.innerHTML = `
                    <span class="element-name">${elementName}</span>
                    <input type="number" class="element-value-input" value="${value}" step="0.01">
                    <span style="font-size: 10px; color: var(--text-color);">%</span>
                    <button class="remove-weapon-element-btn" type="button">X</button>
                `;

                // Update data attribute when value changes
                const valueInput = elementItem.querySelector('.element-value-input');
                valueInput.addEventListener('input', function() {
                    elementItem.dataset.value = this.value;
                });

                elementItem.querySelector('.remove-weapon-element-btn').addEventListener('click', function() {
                    weaponElements.removeChild(elementItem);
                });
                weaponElements.appendChild(elementItem);
            }

            // Global click handler to close search results
            document.addEventListener('click', function(e) {
                if (!e.target.closest('.mod-search') && !e.target.closest('.search-results')) {
                    document.querySelectorAll('.search-results').forEach(sr => sr.style.display = 'none');
                }
            });

            document.getElementById('calculate-btn').addEventListener('click', calculateDamage);
            document.getElementById('add-build-btn').addEventListener('click', addBuild);

            function addModToBuild(build, modId, modName) {
                const selectedMods = build.querySelector('.selected-mods-container');
                const modItem = document.createElement('div');
                modItem.className = 'mod-item';
                modItem.innerHTML = `
                    <span class="mod-name">${modName}</span>
                    <button class="remove-mod-btn" data-mod-id="${modId}">X</button>
                `;
                modItem.querySelector('.remove-mod-btn').addEventListener('click', function() {
                    selectedMods.removeChild(modItem);
                });
                selectedMods.appendChild(modItem);
            }

            function addBuffToBuild(build, buffName, buffType) {
                const selectedBuffs = build.querySelector('.selected-buffs-container');

                // Check if buff already exists in this build
                const existingBuffs = selectedBuffs.querySelectorAll('.buff-item');
                for (let item of existingBuffs) {
                    if (item.dataset.buffName === buffName) {
                        return; // Don't add duplicate
                    }
                }

                const buffItem = document.createElement('div');
                buffItem.className = 'mod-item buff-item';
                buffItem.dataset.buffName = buffName;

                // Determine default value based on type
                let defaultValue = 0;
                let step = '0.01';
                if (buffType.includes('int')) {
                    step = '1';
                } else if (buffName === 'final_multiplier') {
                    defaultValue = 1.0;
                }

                buffItem.innerHTML = `
                    <span class="mod-name" style="flex: 1;">${buffName}</span>
                    <input type="number" class="buff-value-input" value="${defaultValue}" step="${step}" style="width: 60px; padding: 2px 4px; background: var(--input-bg); border: 1px solid var(--border-color); border-radius: 3px; color: var(--text-color); font-size: 11px;">
                    <button class="remove-buff-btn">X</button>
                `;

                buffItem.querySelector('.remove-buff-btn').addEventListener('click', function() {
                    selectedBuffs.removeChild(buffItem);
                });

                selectedBuffs.appendChild(buffItem);
            }

            function addBuild() {
                buildIdCounter++;
                const container = document.getElementById('builds-container');
                const lastBuild = container.querySelector('.build:last-child');

                // Clone the last build
                const newBuild = lastBuild.cloneNode(true);
                newBuild.setAttribute('data-build-id', buildIdCounter);

                // Update build title
                const titleDiv = newBuild.querySelector('.build-title');
                titleDiv.textContent = `Build ${buildIdCounter}`;

                // Attach remove button listener
                const removeBtn = newBuild.querySelector('.remove-build-btn');
                removeBtn.addEventListener('click', function() {
                    removeBuild(newBuild);
                });

                // Setup all event listeners for the new build (includes cloned items)
                setupBuildEventListeners(newBuild);

                container.appendChild(newBuild);

                // Populate dropdowns for the new build
                loadEnemyTypes();
                loadElementOptions();

                // Show remove button on all builds if there's more than one
                updateRemoveButtons();
            }

            function removeBuild(buildElement) {
                const container = document.getElementById('builds-container');
                const builds = container.querySelectorAll('.build');

                if (builds.length <= 1) {
                    alert('Cannot remove the last build');
                    return;
                }

                container.removeChild(buildElement);
                updateRemoveButtons();
            }

            function updateRemoveButtons() {
                const container = document.getElementById('builds-container');
                const builds = container.querySelectorAll('.build');

                // Hide remove button only if there's exactly one build
                builds.forEach((build) => {
                    const removeBtn = build.querySelector('.remove-build-btn');
                    if (builds.length > 1) {
                        removeBtn.style.display = 'flex';
                    } else {
                        removeBtn.style.display = 'none';
                    }
                });
            }

            function calculateDamage() {
                const builds = document.querySelectorAll('.build');
                const allCalculations = [];

                // Process each build
                builds.forEach((build, index) => {
                    const buildId = build.getAttribute('data-build-id');
                    const buildName = build.querySelector('.build-title').textContent || `Build ${buildId}`;

                    // Collect weapon elements from the dynamic list and convert from percentage
                    const elements = {};
                    build.querySelectorAll('.element-item').forEach(item => {
                        const elementName = item.dataset.element;
                        const elementValue = parseFloat(item.dataset.value) / 100; // Convert percentage to decimal
                        elements[elementName] = elementValue;
                    });

                    // Get weapon config - need to query within this build
                    const weaponConfig = {
                        damage: parseFloat(build.querySelector('.base-damage-input').value || 100),
                        attack_speed: parseFloat(build.querySelector('.fire-rate-input').value || 1),
                        multishot: parseFloat(build.querySelector('.multishot-input').value || 1),
                        critical_chance: parseFloat(build.querySelector('.crit-chance-input').value || 0) / 100,
                        critical_damage: parseFloat(build.querySelector('.crit-multiplier-input').value || 2),
                        status_chance: parseFloat(build.querySelector('.status-chance-input').value || 0) / 100,
                        elements: elements
                    };

                    // Collect mods
                    const mods = [];
                    build.querySelectorAll('.mod-item:not(.buff-item)').forEach(item => {
                        const modId = item.querySelector('.remove-mod-btn').getAttribute('data-mod-id');
                        if (modId) {
                            mods.push(modId);
                        }
                    });

                    // Get enemy config
                    const enemyConfig = {
                        faction: build.querySelector('.enemy-faction-select').value || 'none',
                        type: build.querySelector('.enemy-type-select').value || 'none'
                    };

                    // Collect in-game buffs
                    const inGameBuffs = {};
                    build.querySelectorAll('.buff-item').forEach(item => {
                        const buffName = item.dataset.buffName;
                        const buffInput = item.querySelector('.buff-value-input');
                        const buffValue = buffInput.value;

                        // Parse value based on type (check step attribute)
                        if (buffInput.step === '1') {
                            inGameBuffs[buffName] = parseInt(buffValue);
                        } else {
                            inGameBuffs[buffName] = parseFloat(buffValue);
                        }
                    });

                    // Create calculation promise for this build
                    const calcPromise = fetch('/api/calculate-damage', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            weapon: weaponConfig,
                            mods: mods,
                            enemy: enemyConfig,
                            in_game_buffs: inGameBuffs
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (!data.success) throw new Error(data.error || 'Calculation failed');
                        return {
                            buildName: buildName,
                            buildId: buildId,
                            data: data
                        };
                    });

                    allCalculations.push(calcPromise);
                });

                // Wait for all calculations to complete
                Promise.all(allCalculations)
                    .then(results => {
                        displayTabbedResults(results);
                    })
                    .catch(error => {
                        console.error('Calculate damage error:', error);
                        alert('Calculation failed: ' + error.message);
                    });
            }

            function displayTabbedResults(results) {
                const tabsContainer = document.getElementById('results-tabs');
                const contentContainer = document.getElementById('results-content-container');

                // Clear existing tabs and content
                tabsContainer.innerHTML = '';
                contentContainer.innerHTML = '';

                // Create tabs and content for each build
                results.forEach((result, index) => {
                    // Create tab
                    const tab = document.createElement('div');
                    tab.className = 'result-tab' + (index === 0 ? ' active' : '');
                    tab.textContent = result.buildName;
                    tab.dataset.buildId = result.buildId;
                    tab.addEventListener('click', function() {
                        switchResultTab(result.buildId);
                    });
                    tabsContainer.appendChild(tab);

                    // Create content
                    const content = document.createElement('div');
                    content.className = 'result-content' + (index === 0 ? ' active' : '');
                    content.dataset.buildId = result.buildId;
                    content.innerHTML = generateResultContent(result.data);
                    contentContainer.appendChild(content);
                });
            }

            function switchResultTab(buildId) {
                // Update tab active state
                document.querySelectorAll('.result-tab').forEach(tab => {
                    if (tab.dataset.buildId === buildId) {
                        tab.classList.add('active');
                    } else {
                        tab.classList.remove('active');
                    }
                });

                // Update content active state
                document.querySelectorAll('.result-content').forEach(content => {
                    if (content.dataset.buildId === buildId) {
                        content.classList.add('active');
                    } else {
                        content.classList.remove('active');
                    }
                });
            }

            function generateResultContent(data) {
                let html = '';

                // Helper function to format numbers
                function formatValue(value) {
                    if (typeof value === 'number') {
                        return value.toFixed(2);
                    }
                    return value;
                }

                // Helper function to format label names
                function formatLabel(key) {
                    return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                }

                // === DAMAGE SECTION ===
                html += '<div style="margin-bottom: 20px;">';
                html += '<h3 style="color: var(--accent-color); margin-bottom: 10px; font-size: 14px;">Damage Output</h3>';
                html += '<div class="results-grid">';

                if (data.damage) {
                    for (const [key, value] of Object.entries(data.damage)) {
                        html += `
                            <div class="result-item">
                                <div class="result-label">${formatLabel(key)}</div>
                                <div class="result-value">${formatValue(value)}</div>
                            </div>
                        `;
                    }
                }
                html += '</div></div>';

                // === ELEMENT BREAKDOWN SECTION ===
                if (data.element_breakdown && Object.keys(data.element_breakdown).length > 0) {
                    html += '<div style="margin-bottom: 20px;">';
                    html += '<h3 style="color: var(--accent-color); margin-bottom: 10px; font-size: 14px;">Element Breakdown</h3>';

                    const totalElem = Object.values(data.element_breakdown).reduce((a, b) => a + b, 0);

                    if (totalElem > 0) {
                        html += '<div class="element-bar">';
                        for (const [elemName, elemValue] of Object.entries(data.element_breakdown)) {
                            if (elemValue > 0) {
                                const percentage = (elemValue / totalElem) * 100;
                                html += `
                                    <div class="element-segment" style="width: ${percentage}%; background-color: ${getElementColor(elemName)};">
                                        ${formatLabel(elemName)}: ${percentage.toFixed(1)}%
                                    </div>
                                `;
                            }
                        }
                        html += '</div>';
                    } else {
                        html += '<div style="padding: 8px; text-align: center; color: #888;">No elemental damage</div>';
                    }
                    html += '</div>';
                }

                // === STATS SECTION (Secondary) ===
                html += '<div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid var(--border-color);">';
                html += '<h3 style="color: #888; margin-bottom: 10px; font-size: 13px;">Final Stats</h3>';
                html += '<div class="results-grid stats-grid">';

                if (data.stats) {
                    for (const [key, value] of Object.entries(data.stats)) {
                        if (typeof value !== 'object') {
                            html += `
                                <div class="result-item stat-item">
                                    <div class="result-label">${formatLabel(key)}</div>
                                    <div class="result-value">${formatValue(value)}</div>
                                </div>
                            `;
                        }
                    }
                }
                html += '</div></div>';

                html += '<div style="margin-bottom: 20px;">';
                html += `<h3 style="color: var(--accent-color); margin-bottom: 10px; font-size: 14px;">Simulated Statistics (${data.simulation_result.num_simulations} runs × ${data.simulation_result.duration}s)</h3>`;

                // Direct DPS Stats
                if (data.simulation_result.simulated_stats.direct_dps) {
                    html += '<div style="margin-bottom: 15px;">';
                    html += '<h4 style="color: var(--text-secondary); margin-bottom: 8px; font-size: 13px;">Direct DPS</h4>';
                    html += `<div style="padding: 4px 8px;">Min: ${data.simulation_result.simulated_stats.direct_dps.min.toFixed(2)}</div>`;
                    html += `<div style="padding: 4px 8px;">Average: ${data.simulation_result.simulated_stats.direct_dps.avg.toFixed(2)}</div>`;
                    html += `<div style="padding: 4px 8px;">Max: ${data.simulation_result.simulated_stats.direct_dps.max.toFixed(2)}</div>`;
                    html += '</div>';
                }

                // DOT DPS Stats
                if (data.simulation_result.simulated_stats.dot_dps) {
                    html += '<div style="margin-bottom: 15px;">';
                    html += '<h4 style="color: var(--text-secondary); margin-bottom: 8px; font-size: 13px;">DOT DPS</h4>';
                    html += `<div style="padding: 4px 8px;">Min: ${data.simulation_result.simulated_stats.dot_dps.min.toFixed(2)}</div>`;
                    html += `<div style="padding: 4px 8px;">Average: ${data.simulation_result.simulated_stats.dot_dps.avg.toFixed(2)}</div>`;
                    html += `<div style="padding: 4px 8px;">Max: ${data.simulation_result.simulated_stats.dot_dps.max.toFixed(2)}</div>`;
                    html += '</div>';
                }

                // Total DPS Stats
                if (data.simulation_result.simulated_stats.total_dps) {
                    html += '<div style="margin-bottom: 15px;">';
                    html += '<h4 style="color: var(--text-secondary); margin-bottom: 8px; font-size: 13px;">Total DPS</h4>';
                    html += `<div style="padding: 4px 8px;">Min: ${data.simulation_result.simulated_stats.total_dps.min.toFixed(2)}</div>`;
                    html += `<div style="padding: 4px 8px;">Average: ${data.simulation_result.simulated_stats.total_dps.avg.toFixed(2)}</div>`;
                    html += `<div style="padding: 4px 8px;">Max: ${data.simulation_result.simulated_stats.total_dps.max.toFixed(2)}</div>`;
                    html += '</div>';
                }

                html += '</div>';

                return html;
            }

            function getElementColor(elemName) {
                const colors = {
                    impact: '#7A9FAB',      // grey-ish blue
                    puncture: '#B8B888',    // greyish yellow
                    slash: '#B87A7A',       // greyish red
                    cold: '#4A9EFF',        // blue
                    electricity: '#A020F0', // purple
                    heat: '#FF8C00',        // orange
                    toxin: '#4CAF50',       // green
                    blast: '#A52A2A',       // dark red
                    corrosive: '#ADFF2F',   // green-yellow
                    gas: '#48D1CC',         // green-blue
                    magnetic: '#999999',    // grey
                    radiation: '#FFD700',   // yellow
                    viral: '#FF69B4'        // pink
                };
                return colors[elemName] || '#666';
            }
        });