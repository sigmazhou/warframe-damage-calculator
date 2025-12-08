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
            let rivenStats = {};  // Stores riven base stats by weapon type

            /**
             * Format a stat/mod name for display by replacing underscores with spaces
             * @param {string} name - The internal name with underscores
             * @param {boolean} titleCase - Whether to capitalize each word (default: false)
             * @returns {string} Display name with spaces
             */
            function formatDisplayName(name, titleCase = false) {
                const formatted = name.replace(/_/g, ' ');
                if (titleCase) {
                    return formatted.replace(/\b\w/g, l => l.toUpperCase());
                }
                return formatted;
            }

            /**
             * Get match priority for search (lower = better match)
             * @param {string} name - The internal name (e.g., "hornet_strike")
             * @param {string} query - The search query (may contain spaces or underscores)
             * @returns {number} Match priority: 0 = prefix match, 1 = contains match, -1 = no match
             */
            function getSearchMatchPriority(name, query) {
                const normalizedName = name.toLowerCase();
                const normalizedQuery = query.toLowerCase();
                const queryWithUnderscores = normalizedQuery.replace(/ /g, '_');
                const nameWithSpaces = normalizedName.replace(/_/g, ' ');

                // Check prefix match (highest priority)
                if (normalizedName.startsWith(queryWithUnderscores) ||
                    nameWithSpaces.startsWith(normalizedQuery)) {
                    return 0;
                }

                // Check contains match (lower priority)
                if (normalizedName.includes(queryWithUnderscores) ||
                    nameWithSpaces.includes(normalizedQuery)) {
                    return 1;
                }

                return -1; // No match
            }

            loadEnemyTypes();
            loadElementOptions();
            initializeDefaultElements();
            loadAvailableBuffs();
            loadRivenStats();

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

            /**
             * Setup a searchable dropdown for any data source
             * @param {HTMLElement} searchInput - The input element for searching
             * @param {HTMLElement} searchResults - The container for search results
             * @param {Function} getItems - Function that returns array of items with 'name' property
             * @param {Function} onSelect - Callback when an item is selected (receives item, searchInput)
             * @param {Object} options - Configuration options
             * @param {boolean} options.clearOnSelect - Clear input after selection (default: true)
             * @param {string} options.noResultsMessage - Message when no results (default: 'No results found')
             * @param {Function} options.formatDisplay - Function to format display text (default: item.name)
             * @param {Function} options.onInputChange - Called before filtering, can modify behavior (optional)
             */
            function setupSearchableDropdown(searchInput, searchResults, getItems, onSelect, options = {}) {
                const {
                    clearOnSelect = true,
                    noResultsMessage = 'No results found',
                    formatDisplay = (item) => formatDisplayName(item.name),
                    onInputChange = null
                } = options;

                // Search functionality
                searchInput.addEventListener('input', function() {
                    const query = this.value.trim().toLowerCase();

                    // Allow custom input change handling
                    if (onInputChange) {
                        onInputChange(this, query);
                    }

                    if (query.length < 1) {
                        searchResults.style.display = 'none';
                        return;
                    }

                    // Get available items from data source
                    const items = getItems();

                    if (items.length === 0) {
                        searchResults.innerHTML = `<div class="search-result-item">${noResultsMessage}</div>`;
                        searchResults.style.display = 'block';
                        return;
                    }

                    // Filter and sort items (prefix matches first, then contains matches)
                    const matchingItems = items
                        .map(item => ({ item, priority: getSearchMatchPriority(item.name, query) }))
                        .filter(entry => entry.priority >= 0)
                        .sort((a, b) => a.priority - b.priority)
                        .map(entry => entry.item);

                    // Render results
                    searchResults.innerHTML = '';
                    if (matchingItems.length === 0) {
                        searchResults.innerHTML = `<div class="search-result-item">${noResultsMessage}</div>`;
                    } else {
                        matchingItems.forEach(item => {
                            const resultItem = document.createElement('div');
                            resultItem.className = 'search-result-item';
                            resultItem.textContent = formatDisplay(item);
                            resultItem.addEventListener('click', function() {
                                onSelect(item, searchInput);
                                if (clearOnSelect) {
                                    searchInput.value = '';
                                }
                                searchResults.style.display = 'none';
                            });
                            searchResults.appendChild(resultItem);
                        });
                    }
                    searchResults.style.display = 'block';
                });

                // Hide results when clicking outside
                searchInput.addEventListener('blur', function() {
                    setTimeout(() => {
                        searchResults.style.display = 'none';
                    }, 200);
                });

                // Show results when focusing if there's a query
                searchInput.addEventListener('focus', function() {
                    if (this.value.trim().length >= 1) {
                        this.dispatchEvent(new Event('input'));
                    }
                });
            }

            /**
             * Helper to reattach a remove button with a new click handler
             * @param {HTMLElement} item - The item containing the remove button
             * @param {string} buttonSelector - Selector for the remove button
             * @param {Function} onClickHandler - Click handler function
             */
            function reattachRemoveButton(item, buttonSelector, onClickHandler) {
                const removeBtn = item.querySelector(buttonSelector);
                if (removeBtn) {
                    const newBtn = removeBtn.cloneNode(true);
                    removeBtn.parentNode.replaceChild(newBtn, removeBtn);
                    newBtn.addEventListener('click', onClickHandler);
                }
            }

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

                        // Check if query matches "riven" (prefix search)
                        if ('riven'.startsWith(query.toLowerCase())) {
                            searchResults.innerHTML = '';
                            const rivenItem = document.createElement('div');
                            rivenItem.className = 'search-result-item';
                            rivenItem.textContent = 'Riven Mod (Special)';
                            rivenItem.style.fontWeight = 'bold';
                            rivenItem.style.color = 'var(--accent-color)';
                            rivenItem.addEventListener('click', function() {
                                addRivenToBuild(build);
                                modSearch.value = '';
                                searchResults.style.display = 'none';
                            });
                            searchResults.appendChild(rivenItem);
                            searchResults.style.display = 'block';
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
                                        item.textContent = formatDisplayName(mod.name);
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
                    setupSearchableDropdown(
                        buffSearch,
                        buffSearchResults,
                        () => availableBuffs,
                        (buff) => addBuffToBuild(build, buff.name, buff.type),
                        {
                            clearOnSelect: true,
                            noResultsMessage: 'No buffs found'
                        }
                    );
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
                    reattachRemoveButton(item, '.remove-weapon-element-btn', () => {
                        weaponElements.removeChild(item);
                    });

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
                build.querySelectorAll('.mod-item:not(.buff-item):not(.riven-item)').forEach(item => {
                    reattachRemoveButton(item, '.remove-mod-btn', () => {
                        selectedMods.removeChild(item);
                    });
                });

                // Reattach riven event listeners (remove button + stat search dropdowns + roll buttons)
                build.querySelectorAll('.riven-item').forEach(rivenItem => {
                    reattachRemoveButton(rivenItem, '.remove-mod-btn', () => {
                        selectedMods.removeChild(rivenItem);
                    });

                    // Reattach roll button event listeners
                    rivenItem.querySelectorAll('.riven-roll-btn').forEach(btn => {
                        const newBtn = btn.cloneNode(true);
                        btn.parentNode.replaceChild(newBtn, btn);
                        newBtn.addEventListener('click', function(e) {
                            e.preventDefault();
                            e.stopPropagation();
                            const rollType = this.dataset.rollType;
                            generateRivenRoll(rivenItem, build, rollType);
                        });
                    });

                    // Reattach sign toggle button event listeners
                    rivenItem.querySelectorAll('.riven-stat-sign-btn').forEach(btn => {
                        const newBtn = btn.cloneNode(true);
                        btn.parentNode.replaceChild(newBtn, btn);
                        newBtn.addEventListener('click', function(e) {
                            e.preventDefault();
                            e.stopPropagation();
                            const statRow = this.closest('.riven-stat-row');
                            const isNegative = statRow.dataset.isNegative === 'true';
                            statRow.dataset.isNegative = (!isNegative).toString();
                            updateAllRivenRollPercents(rivenItem, build);
                            this.textContent = isNegative ? '+' : '-';
                        });
                    });

                    // Reattach searchable stat selector listeners using riven stats
                    rivenItem.querySelectorAll('.riven-stat-search-input').forEach(searchInput => {
                        const index = searchInput.dataset.statIndex;
                        const statRow = rivenItem.querySelector(`.riven-stat-row[data-stat-index="${index}"]`);
                        const searchResults = statRow.querySelector('.riven-stat-search-results');
                        const valueInput = rivenItem.querySelector(`.riven-stat-value[data-stat-index="${index}"]`);

                        // Initialize selected stat tracking if not already set
                        if (!searchInput.dataset.selectedStat) {
                            searchInput.dataset.selectedStat = '';
                        }

                        // Reattach value input listener for roll percentage update
                        valueInput.addEventListener('input', function() {
                            updateAllRivenRollPercents(rivenItem, build);
                        });

                        // Reattach slider input listener
                        const slider = statRow.querySelector('.riven-roll-slider');
                        slider.addEventListener('input', function() {
                            const percent = parseFloat(this.value);
                            updateRivenStatFromSlider(rivenItem, build, parseInt(index), percent);
                        });

                        // Setup searchable dropdown with riven stats from weapon type
                        setupSearchableDropdown(
                            searchInput,
                            searchResults,
                            () => getAvailableRivenStatsForBuild(build),
                            (stat, input) => {
                                input.value = formatDisplayName(stat.name);
                                input.dataset.selectedStat = stat.name;
                                valueInput.disabled = false;
                                if (!valueInput.value) {
                                    valueInput.value = 0;
                                }
                                updateAllRivenRollPercents(rivenItem, build);
                                valueInput.focus();
                            },
                            {
                                clearOnSelect: false,
                                noResultsMessage: 'No stats found',
                                onInputChange: (input, query) => {
                                    if (input.dataset.selectedStat && input.value !== formatDisplayName(input.dataset.selectedStat)) {
                                        input.dataset.selectedStat = '';
                                        valueInput.disabled = true;
                                        valueInput.value = '';
                                        updateAllRivenRollPercents(rivenItem, build);
                                    }
                                }
                            }
                        );
                    });
                });

                // Reattach buff remove buttons
                const selectedBuffs = build.querySelector('.selected-buffs-container');
                build.querySelectorAll('.buff-item').forEach(item => {
                    reattachRemoveButton(item, '.remove-buff-btn', () => {
                        selectedBuffs.removeChild(item);
                    });
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
                                // Save current value before repopulating
                                const currentValue = factionSelect.value;

                                factionSelect.innerHTML = '';
                                data.enemy_factions.forEach(faction => {
                                    const option = document.createElement('option');
                                    option.value = faction;
                                    option.textContent = faction.charAt(0).toUpperCase() + faction.slice(1);
                                    factionSelect.appendChild(option);
                                });

                                // Restore previous value if it exists in the new options
                                if (currentValue) {
                                    factionSelect.value = currentValue;
                                }
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
                                // Save current value before repopulating
                                const currentValue = typeSelect.value;

                                typeSelect.innerHTML = '';
                                data.enemy_types.forEach(type => {
                                    const option = document.createElement('option');
                                    option.value = type;
                                    option.textContent = type.charAt(0).toUpperCase() + type.slice(1);
                                    typeSelect.appendChild(option);
                                });

                                // Restore previous value if it exists in the new options
                                if (currentValue) {
                                    typeSelect.value = currentValue;
                                }
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

            function loadRivenStats() {
                fetch('/api/riven-stats')
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            rivenStats = data.riven_stats;
                            // Populate weapon type dropdowns
                            const weaponTypes = Object.keys(rivenStats);
                            const weaponTypeSelects = document.querySelectorAll('.weapon-type-select');
                            weaponTypeSelects.forEach(select => {
                                // Save current value before repopulating (default to 'rifle')
                                const currentValue = select.value || 'rifle';
                                select.innerHTML = '';
                                weaponTypes.forEach(type => {
                                    const option = document.createElement('option');
                                    option.value = type;
                                    option.textContent = type.charAt(0).toUpperCase() + type.slice(1);
                                    select.appendChild(option);
                                });
                                // Restore previous value or default to rifle
                                select.value = currentValue;
                            });
                        }
                    })
                    .catch(error => console.error('Load riven stats failed:', error));
            }

            /**
             * Get available riven stats for the selected weapon type in a build
             * @param {HTMLElement} build - The build element
             * @returns {Array} Array of stat objects with name property
             */
            function getAvailableRivenStatsForBuild(build) {
                const weaponType = build.querySelector('.weapon-type-select').value;
                if (!weaponType || !rivenStats[weaponType]) {
                    return [];
                }
                // Convert riven stats object to array of {name: statName} objects
                return Object.keys(rivenStats[weaponType]).map(statName => ({ name: statName }));
            }

            /**
             * Get riven configuration from riven item element, including positive/negative count, disposition, etc.
             * @param {HTMLElement} rivenItem - The riven item DOM element
             * @param {HTMLElement} build - The build containing the riven
             * @returns {Object|null} Configuration object or null if invalid
             */
            function getRivenConfig(rivenItem, build) {
                const weaponType = build.querySelector('.weapon-type-select').value;
                const disposition = parseFloat(build.querySelector('.weapon-disposition-input').value) || 1.0;

                if (!weaponType || !rivenStats[weaponType]) {
                    return null;
                }

                const statRows = rivenItem.querySelectorAll('.riven-stat-row');
                const stats = [];
                let positiveCount = 0;
                let negativeCount = 0;

                statRows.forEach((row, index) => {
                    const searchInput = row.querySelector('.riven-stat-search-input');
                    const valueInput = row.querySelector('.riven-stat-value');
                    const statName = searchInput.dataset.selectedStat;
                    const isNegative = row.dataset.isNegative === 'true';

                    if (statName) {
                        if (isNegative) {
                            negativeCount++;
                        } else {
                            positiveCount++;
                        }
                    }

                    stats.push({
                        index: index,
                        row: row,
                        statName: statName,
                        searchInput: searchInput,
                        valueInput: valueInput,
                        isNegative: isNegative
                    });
                });

                return {
                    weaponType,
                    disposition,
                    positiveCount,
                    negativeCount,
                    stats
                };
            }

            /**
             * Calculate riven stat value based on roll type, stat configuration, and disposition
             *
             * Riven multipliers based on stat count:
             * - 2 positive 0 negative: 0.99 * base
             * - 2 positive 1 negative: 1.2375 for pos, -0.495 for neg
             * - 3 positive 0 negative: 0.75 for pos
             * - 3 positive 1 negative: 0.9375 for pos, -0.75 for neg
             *
             * Roll ranges:
             * - Min: 0.9 * avg
             * - Max: 1.1 * avg
             *
             * @param {string} statName - The riven stat name (e.g., heat_damage, critical_chance)
             * @param {string} weaponType - The weapon type (rifle, shotgun, etc.)
             * @param {number} disposition - The weapon's riven disposition
             * @param {number} positiveCount - Number of positive stats (2 or 3)
             * @param {number} negativeCount - Number of negative stats (0 or 1)
             * @param {boolean} isNegative - Whether this stat is the negative one
             * @param {string} rollType - 'min', 'avg', or 'max'
             * @returns {number|null} The calculated stat value or null if not available
             */
            function calculateRivenStatValue(statName, weaponType, disposition, positiveCount, negativeCount, isNegative, rollType) {
                if (!rivenStats[weaponType]) return null;

                const baseValue = rivenStats[weaponType][statName];
                if (baseValue === undefined) return null;

                const hasNegative = negativeCount > 0;

                // Determine the multiplier based on stat configuration
                let multiplier;
                if (isNegative) {
                    // Negative stat multipliers
                    if (positiveCount === 2 && hasNegative) {
                        multiplier = -0.495;
                    } else if (positiveCount === 3 && hasNegative) {
                        multiplier = -0.75;
                    } else {
                        return null; // Invalid configuration for negative
                    }
                } else {
                    // Positive stat multipliers
                    if (positiveCount === 2 && !hasNegative) {
                        multiplier = 0.99;
                    } else if (positiveCount === 2 && hasNegative) {
                        multiplier = 1.2375;
                    } else if (positiveCount === 3 && !hasNegative) {
                        multiplier = 0.75;
                    } else if (positiveCount === 3 && hasNegative) {
                        multiplier = 0.9375;
                    } else {
                        return null; // Invalid configuration
                    }
                }

                // Calculate average value (base * multiplier * disposition)
                const avgValue = baseValue * multiplier * disposition;

                // Apply roll type modifier
                switch (rollType) {
                    case 'min':
                        return avgValue * 0.9;
                    case 'max':
                        return avgValue * 1.1;
                    case 'avg':
                    default:
                        return avgValue;
                }
            }

            /**
             * Update all roll percentages in a riven item
             * Uses getRivenConfig to get consistent configuration for all stats
             * @param {HTMLElement} rivenItem - The riven item DOM element
             * @param {HTMLElement} build - The build containing the riven
             */
            function updateAllRivenRollPercents(rivenItem, build) {
                const config = getRivenConfig(rivenItem, build);
                if (!config) return;

                config.stats.forEach(stat => {
                    const percentSpan = stat.row.querySelector('.riven-roll-percent');
                    const slider = stat.row.querySelector('.riven-roll-slider');

                    if (!stat.statName || !stat.valueInput.value) {
                        percentSpan.textContent = '';
                        slider.disabled = true;
                        slider.value = 0;
                        return;
                    }

                    const avgValue = calculateRivenStatValue(
                        stat.statName,
                        config.weaponType,
                        config.disposition,
                        config.positiveCount,
                        config.negativeCount,
                        stat.isNegative,
                        'avg'
                    );

                    if (avgValue === null || avgValue === 0) {
                        percentSpan.textContent = '';
                        slider.disabled = true;
                        slider.value = 0;
                        return;
                    }

                    const currentValue = parseFloat(stat.valueInput.value);
                    // For negative stats, compare absolute values since we force negative
                    const percentFromAvg = stat.isNegative
                        ? ((Math.abs(currentValue) / Math.abs(avgValue)) - 1) * 100
                        : ((currentValue / avgValue) - 1) * 100;

                    // Update slider
                    slider.disabled = false;
                    slider.value = Math.max(-10, Math.min(10, percentFromAvg));

                    // Display with sign and color (always show + for non-negative)
                    // For negative stats, reverse the color (higher abs value = worse)
                    percentSpan.textContent = `+${percentFromAvg.toFixed(1)}%`.replace('+-', '-');
                    const isGood = stat.isNegative ? percentFromAvg < 0 : percentFromAvg >= 0;
                    percentSpan.style.color = isGood ? '#4a9' : '#a94';
                });
            }

            /**
             * Update a single riven stat value based on slider percentage
             * @param {HTMLElement} rivenItem - The riven item DOM element
             * @param {HTMLElement} build - The build containing the riven
             * @param {number} statIndex - The stat row index
             * @param {number} percent - The roll percentage (-10 to +10)
             */
            function updateRivenStatFromSlider(rivenItem, build, statIndex, percent) {
                const config = getRivenConfig(rivenItem, build);
                if (!config) return;

                const stat = config.stats[statIndex];
                if (!stat || !stat.statName) return;

                const avgValue = calculateRivenStatValue(
                    stat.statName,
                    config.weaponType,
                    config.disposition,
                    config.positiveCount,
                    config.negativeCount,
                    stat.isNegative,
                    'avg'
                );

                if (avgValue === null) return;

                // Calculate new value from percentage
                const newValue = avgValue * (1 + percent / 100);
                stat.valueInput.value = Math.round(newValue * 1000) / 1000;

                // Update display directly (more efficient than recalculating all stats)
                const percentSpan = stat.row.querySelector('.riven-roll-percent');
                percentSpan.textContent = `+${percent.toFixed(1)}%`.replace('+-', '-');
                const isGood = stat.isNegative ? percent < 0 : percent >= 0;
                percentSpan.style.color = isGood ? '#4a9' : '#a94';
            }

            /**
             * Generate roll values for all stats in a riven item
             * @param {HTMLElement} rivenItem - The riven item DOM element
             * @param {HTMLElement} build - The build containing the riven
             * @param {string} rollType - 'min', 'avg', or 'max'
             */
            function generateRivenRoll(rivenItem, build, rollType) {
                const config = getRivenConfig(rivenItem, build);

                if (!config) {
                    alert('Please select a weapon type first');
                    return;
                }

                const selectedStats = config.stats.filter(s => s.statName);

                // Validate configuration (must have 2-3 positives and 0-1 negatives)
                if (config.positiveCount < 2 || config.positiveCount > 3 || config.negativeCount > 1) {
                    alert('Invalid riven configuration. Must have 2-3 positive stats and 0-1 negative stat.');
                    return;
                }

                // Calculate and apply values for each stat
                selectedStats.forEach(stat => {
                    const value = calculateRivenStatValue(
                        stat.statName,
                        config.weaponType,
                        config.disposition,
                        config.positiveCount,
                        config.negativeCount,
                        stat.isNegative,
                        rollType
                    );

                    if (value !== null) {
                        // Round to 3 decimal places for display
                        stat.valueInput.value = Math.round(value * 1000) / 1000;
                        stat.valueInput.disabled = false;
                    }
                });

                // Update roll percentages after applying values
                updateAllRivenRollPercents(rivenItem, build);
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
                modItem.dataset.modId = modId;
                const displayName = formatDisplayName(modName);
                modItem.innerHTML = `
                    <span class="mod-name">${displayName}</span>
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

                const displayName = formatDisplayName(buffName);
                buffItem.innerHTML = `
                    <span class="mod-name" style="flex: 1;">${displayName}</span>
                    <input type="number" class="buff-value-input" value="${defaultValue}" step="${step}" style="width: 60px; padding: 2px 4px; background: var(--input-bg); border: 1px solid var(--border-color); border-radius: 3px; color: var(--text-color); font-size: 11px;">
                    <button class="remove-buff-btn">X</button>
                `;

                buffItem.querySelector('.remove-buff-btn').addEventListener('click', function() {
                    selectedBuffs.removeChild(buffItem);
                });

                selectedBuffs.appendChild(buffItem);
            }

            function addRivenToBuild(build) {
                const selectedMods = build.querySelector('.selected-mods-container');

                // Generate unique riven ID using incrementing counter
                // Get current counter or initialize to 0
                let rivenCounter = parseInt(build.dataset.rivenCounter || '0');
                rivenCounter++;
                build.dataset.rivenCounter = rivenCounter;
                const rivenId = `riven_${rivenCounter}`;

                // Create riven item
                const rivenItem = document.createElement('div');
                rivenItem.className = 'mod-item riven-item';
                rivenItem.dataset.modType = 'riven';
                rivenItem.dataset.rivenId = rivenId;

                // Build riven HTML
                let rivenHTML = `
                    <div class="riven-header">
                        <span class="mod-name" style="font-weight: bold; color: var(--accent-color);">Riven Mod (${rivenId})</span>
                        <div class="riven-roll-buttons">
                            <button type="button" class="riven-roll-btn" data-roll-type="min" title="Min Roll (0.9 × Avg)">Mi</button>
                            <button type="button" class="riven-roll-btn" data-roll-type="avg" title="Average Roll">Av</button>
                            <button type="button" class="riven-roll-btn" data-roll-type="max" title="Max Roll (1.1 × Avg)">Ma</button>
                        </div>
                        <button class="remove-mod-btn" data-mod-id="${rivenId}">X</button>
                    </div>
                    <div class="riven-stats-grid">
                `;

                // Create 4 stat rows with searchable inputs
                for (let i = 0; i < 4; i++) {
                    rivenHTML += `
                        <div class="riven-stat-row" data-stat-index="${i}" data-is-negative="false">
                            <button type="button" class="riven-stat-sign-btn" data-stat-index="${i}" title="Toggle positive/negative">+</button>
                            <div class="riven-stat-search">
                                <input type="text" class="riven-stat-search-input"
                                       placeholder="Search stat..." data-stat-index="${i}">
                                <div class="riven-stat-search-results"></div>
                            </div>
                            <input type="number" class="riven-stat-value" data-stat-index="${i}"
                                   step="0.01" placeholder="Value" disabled>
                            <input type="range" class="riven-roll-slider" data-stat-index="${i}"
                                   min="-10" max="10" step="0.1" value="0" disabled>
                            <span class="riven-roll-percent" data-stat-index="${i}"></span>
                        </div>
                    `;
                }

                rivenHTML += '</div>';
                rivenItem.innerHTML = rivenHTML;

                selectedMods.appendChild(rivenItem);

                // Setup event listeners for all rivens in this build (including the newly added one)
                setupBuildEventListeners(build);
            }

            /**
             * Collect all select values from a build (cloneNode doesn't preserve them)
             * @param {HTMLElement} build - The build element
             * @returns {Map} Map of selector -> value pairs
             */
            function collectSelectValues(build) {
                const values = new Map();
                build.querySelectorAll('select').forEach(select => {
                    // Use a unique identifier based on class or nearby context
                    const key = select.className || select.name || select.id;
                    if (key) {
                        values.set(key, select.value);
                    }
                });
                return values;
            }

            /**
             * Restore select values to a build
             * @param {HTMLElement} build - The build element
             * @param {Map} values - Map of selector -> value pairs
             */
            function restoreSelectValues(build, values) {
                build.querySelectorAll('select').forEach(select => {
                    const key = select.className || select.name || select.id;
                    if (key && values.has(key)) {
                        select.value = values.get(key);
                    }
                });
            }

            /**
             * Sync riven counter based on existing rivens in build
             * @param {HTMLElement} build - The build element
             */
            function syncRivenCounter(build) {
                let maxRivenId = 0;
                build.querySelectorAll('.riven-item').forEach(riven => {
                    const rivenId = riven.dataset.rivenId;
                    if (rivenId && rivenId.startsWith('riven_')) {
                        const num = parseInt(rivenId.replace('riven_', ''));
                        if (num > maxRivenId) maxRivenId = num;
                    }
                });
                build.dataset.rivenCounter = maxRivenId.toString();
            }

            function addBuild() {
                buildIdCounter++;
                const container = document.getElementById('builds-container');
                const lastBuild = container.querySelector('.build:last-child');

                // Save select values (cloneNode doesn't preserve them)
                const selectValues = collectSelectValues(lastBuild);

                // Clone the build
                const newBuild = lastBuild.cloneNode(true);
                newBuild.setAttribute('data-build-id', buildIdCounter);

                // Restore select values
                restoreSelectValues(newBuild, selectValues);

                // Sync riven counter based on cloned rivens
                syncRivenCounter(newBuild);

                // Update build title
                newBuild.querySelector('.build-title').value = `Build ${buildIdCounter}`;

                // Attach remove button listener
                const removeBtn = newBuild.querySelector('.remove-build-btn');
                removeBtn.addEventListener('click', () => removeBuild(newBuild));

                // Setup all event listeners for the new build (handles cloned items)
                setupBuildEventListeners(newBuild);

                container.appendChild(newBuild);

                // Populate dropdowns for the new build
                loadEnemyTypes();
                loadElementOptions();
                loadRivenStats();

                // Update remove button visibility
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
                    const buildName = build.querySelector('.build-title').value || `Build ${buildId}`;

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

                    // Collect mods (including riven IDs)
                    const mods = [];
                    build.querySelectorAll('.mod-item:not(.buff-item)').forEach(item => {
                        const modId = item.querySelector('.remove-mod-btn').getAttribute('data-mod-id');
                        if (modId) {
                            mods.push(modId);
                        }
                    });

                    // Collect rivens data as object with IDs as keys
                    const rivensData = {};
                    build.querySelectorAll('.riven-item').forEach(rivenItem => {
                        const rivenId = rivenItem.dataset.rivenId;
                        const rivenStats = {};

                        rivenItem.querySelectorAll('.riven-stat-search-input').forEach(searchInput => {
                            const statType = searchInput.dataset.selectedStat;
                            if (statType) {
                                const index = searchInput.dataset.statIndex;
                                const statRow = rivenItem.querySelector(`.riven-stat-row[data-stat-index="${index}"]`);
                                const valueInput = rivenItem.querySelector(`.riven-stat-value[data-stat-index="${index}"]`);
                                let value = parseFloat(valueInput.value || 0);

                                // If stat is marked as negative, ensure value is negative
                                const isNegative = statRow && statRow.dataset.isNegative === 'true';
                                if (isNegative) {
                                    value = -Math.abs(value);
                                }

                                // Store as key-value pairs like in-game buffs
                                rivenStats[statType] = value;
                            }
                        });

                        if (Object.keys(rivenStats).length > 0) {
                            rivensData[rivenId] = rivenStats;
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
                    const requestBody = {
                        weapon: weaponConfig,
                        mods: mods,
                        enemy: enemyConfig,
                        in_game_buffs: inGameBuffs
                    };

                    // Add rivens if present
                    if (Object.keys(rivensData).length > 0) {
                        requestBody.rivens = rivensData;
                    }

                    const calcPromise = fetch('/api/calculate-damage', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(requestBody)
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
                document.querySelectorAll('.result-tab').forEach(tab => {
                    tab.classList.toggle('active', tab.dataset.buildId === buildId);
                });
                document.querySelectorAll('.result-content').forEach(content => {
                    content.classList.toggle('active', content.dataset.buildId === buildId);
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
                    return formatDisplayName(key, true);
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