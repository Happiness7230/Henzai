/**
 * Utility Functions
 * Common helper functions used across the application
 */

const Utils = {
    /**
     * Show toast notification
     * @param {string} message - The message to display
     * @param {string} type - Type: success, error, warning, info
     * @param {number} duration - Duration in milliseconds
     */
    showToast(message, type = 'info', duration = 3000) {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        }[type] || 'fa-info-circle';
        
        toast.innerHTML = `
            <i class="fas ${icon}"></i>
            <span>${message}</span>
        `;
        
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },
    
    /**
     * Show loading overlay
     */
    showLoading() {
        document.getElementById('loading-overlay')?.classList.remove('hidden');
    },
    
    /**
     * Hide loading overlay
     */
    hideLoading() {
        document.getElementById('loading-overlay')?.classList.add('hidden');
    },
    
    /**
     * Debounce function
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in milliseconds
     * @returns {Function} Debounced function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    /**
     * Get query parameter from URL
     * @param {string} name - Parameter name
     * @returns {string|null} Parameter value
     */
    getQueryParam(name) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(name);
    },
    
    /**
     * Set query parameter in URL
     * @param {string} name - Parameter name
     * @param {string} value - Parameter value
     */
    setQueryParam(name, value) {
        const url = new URL(window.location);
        url.searchParams.set(name, value);
        window.history.pushState({}, '', url);
    },
    
    /**
     * Format number with commas
     * @param {number} num - Number to format
     * @returns {string} Formatted number
     */
    formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },
    
    /**
     * Format date to relative time
     * @param {string|Date} date - Date to format
     * @returns {string} Relative time string
     */
    formatRelativeTime(date) {
        const now = new Date();
        const diff = now - new Date(date);
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);
        
        if (seconds < 60) return 'just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        return new Date(date).toLocaleDateString();
    },
    
    /**
     * Highlight text matches
     * @param {string} text - Text to highlight
     * @param {string} query - Query to highlight
     * @returns {string} HTML with highlighted text
     */
    highlightText(text, query) {
        if (!query) return text;
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    },
    
    /**
     * Truncate text
     * @param {string} text - Text to truncate
     * @param {number} length - Max length
     * @returns {string} Truncated text
     */
    truncate(text, length) {
        if (text.length <= length) return text;
        return text.substr(0, length) + '...';
    },
    
    /**
     * Extract domain from URL
     * @param {string} url - URL to extract from
     * @returns {string} Domain name
     */
    extractDomain(url) {
        try {
            const urlObj = new URL(url);
            return urlObj.hostname.replace('www.', '');
        } catch {
            return '';
        }
    },
    
    /**
     * Get favicon URL
     * @param {string} url - Website URL
     * @returns {string} Favicon URL
     */
    getFaviconUrl(url) {
        try {
            const domain = this.extractDomain(url);
            return `https://www.google.com/s2/favicons?domain=${domain}&sz=32`;
        } catch {
            return '';
        }
    },
    
    /**
     * Save to localStorage
     * @param {string} key - Storage key
     * @param {any} value - Value to store
     */
    saveToStorage(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (e) {
            console.error('Failed to save to storage:', e);
        }
    },
    
    /**
     * Get from localStorage
     * @param {string} key - Storage key
     * @param {any} defaultValue - Default value if not found
     * @returns {any} Stored value
     */
    getFromStorage(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.error('Failed to get from storage:', e);
            return defaultValue;
        }
    },
    
    /**
     * Copy text to clipboard
     * @param {string} text - Text to copy
     * @returns {Promise<boolean>} Success status
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showToast('Copied to clipboard', 'success');
            return true;
        } catch (e) {
            this.showToast('Failed to copy', 'error');
            return false;
        }
    },
    
    /**
     * Check if dark mode is enabled
     * @returns {boolean} Dark mode status
     */
    isDarkMode() {
        return document.documentElement.getAttribute('data-theme') === 'dark';
    },
    
    /**
     * Toggle dark mode
     */
    toggleDarkMode() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        this.saveToStorage('theme', newTheme);
        
        // Update icon
        const icon = document.querySelector('#darkModeBtn i');
        if (icon) {
            icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    },
    
    /**
     * Initialize dark mode from storage
     */
    initDarkMode() {
        const savedTheme = this.getFromStorage('theme', 'light');
        document.documentElement.setAttribute('data-theme', savedTheme);
        
        // Update icon
        const icon = document.querySelector('#darkModeBtn i');
        if (icon) {
            icon.className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    },
    
    /**
     * Smooth scroll to element
     * @param {string} selector - Element selector
     */
    scrollTo(selector) {
        const element = document.querySelector(selector);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    },
    
    /**
     * Generate unique ID
     * @returns {string} Unique ID
     */
    generateId() {
        return `_${Math.random().toString(36).substr(2, 9)}`;
    },
    
    /**
     * Validate email
     * @param {string} email - Email to validate
     * @returns {boolean} Validity status
     */
    isValidEmail(email) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    },
    
    /**
     * Validate URL
     * @param {string} url - URL to validate
     * @returns {boolean} Validity status
     */
    isValidUrl(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    }
};

// Initialize dark mode on load
document.addEventListener('DOMContentLoaded', () => {
    Utils.initDarkMode();
    
    // Setup dark mode toggle
    const darkModeBtn = document.getElementById('darkModeBtn');
    if (darkModeBtn) {
        darkModeBtn.addEventListener('click', () => Utils.toggleDarkMode());
    }
});

// Export for use in other scripts
window.Utils = Utils;