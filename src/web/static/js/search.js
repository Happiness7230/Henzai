/**
 * FIXED search.js - Add this to handle results page
 */

// Add this new function to handle the results page
function initResultsPage() {
    // Check if we're on the results page
    if (window.location.pathname === '/results') {
        const urlParams = new URLSearchParams(window.location.search);
        const query = urlParams.get('q');
        const mode = urlParams.get('mode') || 'hybrid';
        
        if (query) {
            console.log(`Loading results for: ${query}, mode: ${mode}`);
            fetchAndDisplayResults(query, mode);
        }
    }
}

// New function to fetch and display results
async function fetchAndDisplayResults(query, mode) {
    const resultsContainer = document.getElementById('search-results');
    
    if (!resultsContainer) {
        console.error('Results container not found');
        return;
    }
    
    // Show loading state
    resultsContainer.innerHTML = '<div class="loading">Searching...</div>';
    
    try {
        // Determine max results: prefer URL param, then local preference, then default 20
        const urlParams = new URLSearchParams(window.location.search);
        const maxResults = urlParams.get('max_results') || localStorage.getItem('maxResults') || 20;

        // Call the backend API
        const response = await fetch(
            `/api/search?q=${encodeURIComponent(query)}&mode=${mode}&max_results=${encodeURIComponent(maxResults)}`
        );
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        console.log('Search results:', data);
        
        // Check if we got results
        if (data.status === 'success' && data.data) {
            displaySearchResults(data.data, resultsContainer);
        } else {
            resultsContainer.innerHTML = `
                <div class="no-results">
                    <p>No results found for "${query}"</p>
                </div>
            `;
        }
        
    } catch (error) {
        console.error('Search error:', error);
        resultsContainer.innerHTML = `
            <div class="error">
                <p>Search failed: ${error.message}</p>
                <p>Please try again or check your connection.</p>
            </div>
        `;
    }
}

// Function to display results
function displaySearchResults(data, container) {
    container.innerHTML = '';
    
    const results = data.results || [];
    
    if (results.length === 0) {
        container.innerHTML = `
            <div class="no-results">
                <p>No results found for "${data.query}"</p>
            </div>
        `;
        return;
    }
    
    // Display answer box if available
    if (data.answer_box) {
        const answerBox = document.createElement('div');
        answerBox.className = 'answer-box';
        answerBox.innerHTML = `
            <h3>${data.answer_box.title || 'Answer'}</h3>
            <p>${data.answer_box.answer || data.answer_box.snippet || ''}</p>
        `;
        container.appendChild(answerBox);
    }
    
    // Display knowledge graph if available
    if (data.knowledge_graph) {
        const kg = document.createElement('div');
        kg.className = 'knowledge-graph';
        kg.innerHTML = `
            <h3>${data.knowledge_graph.title || ''}</h3>
            <p>${data.knowledge_graph.description || ''}</p>
            ${data.knowledge_graph.image ? `<img src="${data.knowledge_graph.image}" alt="${data.knowledge_graph.title}">` : ''}
        `;
        container.appendChild(kg);
    }
    
    // Display search results
    results.forEach((result, index) => {
        const resultElement = createResultElement(result, index + 1);
        container.appendChild(resultElement);
    });
    
    // Display related searches if available
    if (data.related_searches && data.related_searches.length > 0) {
        const relatedDiv = document.createElement('div');
        relatedDiv.className = 'related-searches';
        relatedDiv.innerHTML = '<h3>Related Searches</h3>';
        
        const relatedList = document.createElement('ul');
        data.related_searches.forEach(related => {
            const li = document.createElement('li');
            li.innerHTML = `<a href="/results?q=${encodeURIComponent(related)}">${related}</a>`;
            relatedList.appendChild(li);
        });
        
        relatedDiv.appendChild(relatedList);
        container.appendChild(relatedDiv);
    }
}

function createResultElement(result, position) {
    const div = document.createElement('div');
    div.className = 'search-result';
    
    const favicon = result.favicon ? 
        `<img src="${result.favicon}" alt="" class="favicon">` : '';
    
    const source = result.source ? 
        `<span class="source-badge">${result.source}</span>` : '';
    
    div.innerHTML = `
        <div class="result-header">
            ${favicon}
            <cite>${result.domain || new URL(result.url).hostname}</cite>
            ${source}
        </div>
        <h3>
            <a href="${result.url}" target="_blank" rel="noopener noreferrer">
                ${result.title}
            </a>
        </h3>
        <p class="snippet">${result.snippet || ''}</p>
        ${result.date ? `<time>${result.date}</time>` : ''}
    `;
    
    return div;
}
/**
 * GLOBAL SEARCH FUNCTIONS (added safely without breaking existing code)
 */
let currentSearchMode = 'hybrid';

function runSearch(query, mode) {
    if (!query) return;

    console.log(`runSearch called: "${query}" in mode: ${mode}`);

    // Google CSE mode
    if (mode === 'google') {
        if (window.google?.search?.cse) {
            window.google.search.cse.element.execute(query);
            console.log('Google CSE search triggered');
        } else {
            console.error('Google CSE not loaded');
        }
        return;
    }

    // Include user's preferred max_results from localStorage (default 20)
    const maxResults = localStorage.getItem('maxResults') || 20;

    // Redirect to results page for hybrid / local / web modes
    const url = `/results?q=${encodeURIComponent(query)}&mode=${mode}&max_results=${encodeURIComponent(maxResults)}`;
    window.location.href = url;
}

function switchSearchMode(mode) {
    currentSearchMode = mode;
    console.log(`Mode switched to: ${mode}`);

    const modeButtons = document.querySelectorAll('.mode-btn');
    modeButtons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === mode);
    });

    // Toggle Google CSE visibility
    const googleElement = document.querySelector('.gcse-search');
    if (googleElement) {
        googleElement.style.display = mode === 'google' ? 'block' : 'none';
    }
}

// Update the DOMContentLoaded event
document.addEventListener('DOMContentLoaded', () => {
    // Initialize results page if on results page
    initResultsPage();
    
    // ... rest of your existing DOMContentLoaded code ...
    const searchForm = document.getElementById('searchForm');
    const searchInput = document.getElementById('searchInput');
    const clearBtn = document.getElementById('clearBtn');
    const voiceBtn = document.getElementById('voiceBtn');
    const luckyBtn = document.getElementById('luckyBtn');
    const settingsBtn = document.getElementById('settingsBtn');
    const settingsModal = document.getElementById('settingsModal');
    const closeSettings = document.getElementById('closeSettings');
    const modeButtons = document.querySelectorAll('.mode-btn');
    
    // Only run these if we're on the search page (not results page)
    if (searchForm) {
        // Ensure the Google element is hidden on load if the default mode isn't 'google'
        const googleElement = document.querySelector('.gcse-search');
        if (googleElement) {
            if (currentSearchMode !== 'google') {
                googleElement.style.display = 'none';
            }
        }
        
        // Handle search form submission
        searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const query = searchInput.value.trim();
            if (query) {
                runSearch(query, currentSearchMode);
            }
        });
        
        // Handle input changes
        if (searchInput) {
            searchInput.addEventListener('input', () => {
                if (clearBtn) {
                    clearBtn.classList.toggle('hidden', !searchInput.value);
                }
            });
        }
        
        // Clear button
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                searchInput.value = '';
                searchInput.focus();
                clearBtn.classList.add('hidden');
            });
        }
        
        // Voice search
        if (voiceBtn) {
            voiceBtn.addEventListener('click', () => {
                if ('webkitSpeechRecognition' in window) {
                    const recognition = new webkitSpeechRecognition();
                    recognition.lang = 'en-US';
                    voiceBtn.classList.add('listening');
                    
                    recognition.onresult = (event) => {
                        const transcript = event.results[0][0].transcript;
                        searchInput.value = transcript;
                        voiceBtn.classList.remove('listening');
                        runSearch(transcript, currentSearchMode);
                    };
                    
                    recognition.onerror = () => {
                        voiceBtn.classList.remove('listening');
                        if (typeof Utils !== 'undefined') {
                            Utils.showToast('Voice search failed', 'error');
                        }
                    };
                    
                    recognition.start();
                } else {
                    if (typeof Utils !== 'undefined') {
                        Utils.showToast('Voice search not supported', 'warning');
                    }
                }
            });
        }
        
        // I'm Feeling Lucky
        if (luckyBtn) {
            luckyBtn.addEventListener('click', async () => {
                const query = searchInput.value.trim();
                if (!query) return;
                
                if (typeof Utils !== 'undefined') {
                    Utils.showLoading();
                }
                
                try {
                    const response = await fetch(
                        `/api/search?q=${encodeURIComponent(query)}&max_results=1&mode=hybrid`
                    );
                    const data = await response.json();
                    
                    if (data.status === 'success' && data.data.results.length > 0) {
                        window.location.href = data.data.results[0].url;
                    } else {
                        if (typeof Utils !== 'undefined') {
                            Utils.showToast('No results found', 'warning');
                        }
                    }
                } catch (error) {
                    if (typeof Utils !== 'undefined') {
                        Utils.showToast('Search failed', 'error');
                    }
                } finally {
                    if (typeof Utils !== 'undefined') {
                        Utils.hideLoading();
                    }
                }
            });
        }
        
        // Settings modal
        if (settingsBtn && settingsModal && closeSettings) {
            settingsBtn.addEventListener('click', () => {
                settingsModal.classList.remove('hidden');
                // Load current preference and set select value
                const currentPref = localStorage.getItem('maxResults') || '20';
                const select = document.getElementById('maxResultsSelect');
                if (select) {
                    select.value = currentPref;
                }
            });
            
            closeSettings.addEventListener('click', () => {
                settingsModal.classList.add('hidden');
            });
            
            settingsModal.addEventListener('click', (e) => {
                if (e.target === settingsModal) {
                    settingsModal.classList.add('hidden');
                }
            });

            // Results per page setting
            const maxResultsSelect = document.getElementById('maxResultsSelect');
            if (maxResultsSelect) {
                maxResultsSelect.addEventListener('change', (e) => {
                    const value = e.target.value;
                    localStorage.setItem('maxResults', value);
                    console.log(`Max results preference saved: ${value}`);
                });
            }
        }
        
        // Mode selector
        if (modeButtons) {
            modeButtons.forEach(btn => {
                btn.addEventListener('click', async () => {
                    const mode = btn.dataset.mode;
                    const query = searchInput.value.trim();

                    switchSearchMode(mode);

                    try {
                        if (typeof API !== 'undefined') {
                            await API.setSearchMode(mode);
                        }
                    } catch (error) {
                        console.error('Failed to change mode:', error);
                    }
                    
                    if (query) {
                        runSearch(query, mode);
                    }
                });
            });
        }
        
        // Load quick stats
        loadQuickStats();
        
        // Clear cache button
        const clearCacheBtn = document.getElementById('clearCache');
        if (clearCacheBtn) {
            clearCacheBtn.addEventListener('click', async () => {
                try {
                    if (typeof API !== 'undefined') {
                        await API.clearCache();
                        if (typeof Utils !== 'undefined') {
                            Utils.showToast('Cache cleared', 'success');
                        }
                    }
                } catch (error) {
                    if (typeof Utils !== 'undefined') {
                        Utils.showToast('Failed to clear cache', 'error');
                    }
                }
            });
        }
    }
    
    // More search dropdown (works on both pages)
    const moreSearchBtn = document.getElementById('moreSearchBtn');
    const moreSearchMenu = document.getElementById('moreSearchMenu');
    
    if (moreSearchBtn && moreSearchMenu) {
        moreSearchBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            moreSearchMenu.classList.toggle('hidden');
        });
        
        // Dropdown items
        document.querySelectorAll('.dropdown-item').forEach(item => {
            item.addEventListener('click', () => {
                const searchType = item.dataset.searchType;
                const input = document.getElementById('searchInput');
                const query = input ? input.value.trim() : '';
                
                moreSearchMenu.classList.add('hidden');
                
                switch(searchType) {
                    case 'marketplace':
                        window.location.href = `/marketplace?q=${encodeURIComponent(query)}`;
                        break;
                    case 'jobs':
                        window.location.href = `/jobs?q=${encodeURIComponent(query)}`;
                        break;
                    case 'compare':
                        if (typeof Utils !== 'undefined') {
                            Utils.showToast('Select products from marketplace search', 'info');
                        }
                        break;
                    case 'alerts':
                        window.location.href = '/alerts';
                        break;
                    case 'lucky':
                        const lucky = document.getElementById('luckyBtn');
                        if (lucky) lucky.click();
                        break;
                }
            });
        });
        
        // Close dropdown on outside click
        document.addEventListener('click', (e) => {
            if (!moreSearchMenu.contains(e.target) && !moreSearchBtn.contains(e.target)) {
                moreSearchMenu.classList.add('hidden');
            }
        });
    }
});

async function loadQuickStats() {
    try {
        if (typeof API !== 'undefined') {
            const stats = await API.getStats();
            const indexedCount = document.getElementById('indexedCount');
            const searchCount = document.getElementById('searchCount');
            const cacheHitRate = document.getElementById('cacheHitRate');
            
            if (indexedCount) indexedCount.textContent = 'Loading...';
            if (searchCount) {
                searchCount.textContent = 
                    (stats.data.search_stats?.total_searches || '0') + ' searches';
            }
            if (cacheHitRate) {
                cacheHitRate.textContent = 
                    (stats.data.search_stats?.cache_hit_rate || 0).toFixed(1) + '% cache hit';
            }
        }
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}