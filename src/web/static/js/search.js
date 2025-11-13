/**
 * Search Page Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('searchForm');
    const searchInput = document.getElementById('searchInput');
    const clearBtn = document.getElementById('clearBtn');
    const voiceBtn = document.getElementById('voiceBtn');
    const luckyBtn = document.getElementById('luckyBtn');
    const settingsBtn = document.getElementById('settingsBtn');
    const settingsModal = document.getElementById('settingsModal');
    const closeSettings = document.getElementById('closeSettings');
    const modeButtons = document.querySelectorAll('.mode-btn');
    
    // Handle search form submission
    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const query = searchInput.value.trim();
        if (query) {
            window.location.href = `/results?q=${encodeURIComponent(query)}`;
        }
    });
    
    // Handle input changes
    searchInput.addEventListener('input', () => {
        clearBtn.classList.toggle('hidden', !searchInput.value);
    });
    
    // Clear button
    clearBtn.addEventListener('click', () => {
        searchInput.value = '';
        searchInput.focus();
        clearBtn.classList.add('hidden');
    });
    
    // Voice search (placeholder)
    voiceBtn.addEventListener('click', () => {
        if ('webkitSpeechRecognition' in window) {
            const recognition = new webkitSpeechRecognition();
            recognition.lang = 'en-US';
            voiceBtn.classList.add('listening');
            
            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                searchInput.value = transcript;
                voiceBtn.classList.remove('listening');
                searchForm.dispatchEvent(new Event('submit'));
            };
            
            recognition.onerror = () => {
                voiceBtn.classList.remove('listening');
                Utils.showToast('Voice search failed', 'error');
            };
            
            recognition.start();
        } else {
            Utils.showToast('Voice search not supported', 'warning');
        }
    });
    
    // I'm Feeling Lucky
    luckyBtn.addEventListener('click', async () => {
        const query = searchInput.value.trim();
        if (!query) return;
        
        Utils.showLoading();
        try {
            const response = await API.search({ q: query, max_results: 1 });
            if (response.data.results.length > 0) {
                window.location.href = response.data.results[0].url;
            } else {
                Utils.showToast('No results found', 'warning');
            }
        } catch (error) {
            Utils.showToast('Search failed', 'error');
        } finally {
            Utils.hideLoading();
        }
    });
    
    // Settings modal
    settingsBtn.addEventListener('click', () => {
        settingsModal.classList.remove('hidden');
    });
    
    closeSettings.addEventListener('click', () => {
        settingsModal.classList.add('hidden');
    });
    
    settingsModal.addEventListener('click', (e) => {
        if (e.target === settingsModal) {
            settingsModal.classList.add('hidden');
        }
    });
    
    // Mode selector
    modeButtons.forEach(btn => {
        btn.addEventListener('click', async () => {
            const mode = btn.dataset.mode;
            
            try {
                await API.setSearchMode(mode);
                modeButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                Utils.showToast(`Switched to ${mode} mode`, 'success');
            } catch (error) {
                Utils.showToast('Failed to change mode', 'error');
            }
        });
    });
    
    // Load quick stats
    loadQuickStats();
    
    // Clear cache button
    document.getElementById('clearCache')?.addEventListener('click', async () => {
        try {
            await API.clearCache();
            Utils.showToast('Cache cleared', 'success');
        } catch (error) {
            Utils.showToast('Failed to clear cache', 'error');
        }
    });
});

async function loadQuickStats() {
    try {
        const stats = await API.getStats();
        document.getElementById('indexedCount').textContent = 'Loading...';
        document.getElementById('searchCount').textContent = 
            stats.data.search_stats?.total_searches || '0' + ' searches';
        document.getElementById('cacheHitRate').textContent = 
            (stats.data.search_stats?.cache_hit_rate || 0).toFixed(1) + '% cache hit';
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}