/**
 * Filter Logic
 */

const Filters = {
    activeFilters: {},
    
    init() {
        this.setupFilterListeners();
        this.loadSavedFilters();
    },
    
    setupFilterListeners() {
        // Time filter
        const timeFilter = document.getElementById('timeFilter');
        if (timeFilter) {
            timeFilter.addEventListener('change', () => {
                this.activeFilters.time_period = timeFilter.value;
            });
        }
        
        // Source filters
        const localOnly = document.getElementById('localOnly');
        const webOnly = document.getElementById('webOnly');
        
        if (localOnly) {
            localOnly.addEventListener('change', () => {
                if (localOnly.checked) {
                    webOnly.checked = false;
                    this.activeFilters.mode = 'local';
                } else {
                    delete this.activeFilters.mode;
                }
            });
        }
        
        if (webOnly) {
            webOnly.addEventListener('change', () => {
                if (webOnly.checked) {
                    localOnly.checked = false;
                    this.activeFilters.mode = 'serpapi';
                } else {
                    delete this.activeFilters.mode;
                }
            });
        }
    },
    
    getActiveFilters() {
        return this.activeFilters;
    },
    
    clearFilters() {
        this.activeFilters = {};
        document.getElementById('timeFilter').value = '';
        document.getElementById('localOnly').checked = false;
        document.getElementById('webOnly').checked = false;
    },
    
    loadSavedFilters() {
        const saved = Utils.getFromStorage('filters', {});
        this.activeFilters = saved;
        // Apply to UI
        if (saved.time_period) {
            document.getElementById('timeFilter').value = saved.time_period;
        }
    },
    
    saveFilters() {
        Utils.saveToStorage('filters', this.activeFilters);
    }
};

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    Filters.init();
});

window.Filters = Filters;