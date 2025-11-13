/**
 * Autocomplete Logic
 */

let autocompleteTimeout;
let currentSuggestions = [];
let selectedIndex = -1;

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const autocompleteDiv = document.getElementById('autocomplete');
    
    if (!searchInput || !autocompleteDiv) return;
    
    // Input handler with debounce
    searchInput.addEventListener('input', Utils.debounce(async () => {
        const query = searchInput.value.trim();
        
        if (query.length < 2) {
            hideAutocomplete();
            return;
        }
        
        try {
            const suggestions = await API.getSuggestions(query);
            showAutocomplete(suggestions);
        } catch (error) {
            console.error('Autocomplete error:', error);
        }
    }, 300));
    
    // Keyboard navigation
    searchInput.addEventListener('keydown', (e) => {
        if (!currentSuggestions.length) return;
        
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            selectedIndex = Math.min(selectedIndex + 1, currentSuggestions.length - 1);
            updateSelection();
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            selectedIndex = Math.max(selectedIndex - 1, -1);
            updateSelection();
        } else if (e.key === 'Enter' && selectedIndex >= 0) {
            e.preventDefault();
            searchInput.value = currentSuggestions[selectedIndex];
            hideAutocomplete();
        } else if (e.key === 'Escape') {
            hideAutocomplete();
        }
    });
    
    // Click outside to close
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !autocompleteDiv.contains(e.target)) {
            hideAutocomplete();
        }
    });
});

function showAutocomplete(suggestions) {
    const autocompleteDiv = document.getElementById('autocomplete');
    const searchInput = document.getElementById('searchInput');
    
    if (!suggestions || suggestions.length === 0) {
        hideAutocomplete();
        return;
    }
    
    currentSuggestions = suggestions;
    selectedIndex = -1;
    
    autocompleteDiv.innerHTML = '';
    suggestions.forEach((suggestion, index) => {
        const item = document.createElement('div');
        item.className = 'autocomplete-item';
        item.innerHTML = `<i class="fas fa-search"></i><span>${suggestion}</span>`;
        
        item.addEventListener('click', () => {
            searchInput.value = suggestion;
            hideAutocomplete();
            // Trigger search
            const form = searchInput.closest('form');
            if (form) form.dispatchEvent(new Event('submit'));
        });
        
        autocompleteDiv.appendChild(item);
    });
    
    autocompleteDiv.classList.remove('hidden');
}

function hideAutocomplete() {
    const autocompleteDiv = document.getElementById('autocomplete');
    autocompleteDiv.classList.add('hidden');
    currentSuggestions = [];
    selectedIndex = -1;
}

function updateSelection() {
    const items = document.querySelectorAll('.autocomplete-item');
    items.forEach((item, index) => {
        item.classList.toggle('active', index === selectedIndex);
    });
    
    if (selectedIndex >= 0) {
        document.getElementById('searchInput').value = currentSuggestions[selectedIndex];
    }
}