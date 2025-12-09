/**
 * Results Page Logic
 */

let currentPage = 1;
let currentQuery = '';
let currentFilters = {};

document.addEventListener('DOMContentLoaded', () => {
    currentQuery = Utils.getQueryParam('q') || '';
    const searchInput = document.getElementById('searchInput');
    if (searchInput) searchInput.value = currentQuery;
    
    // Initialize
    performSearch();
    setupEventListeners();
});

function setupEventListeners() {
    // Search form
    const searchForm = document.getElementById('searchForm');
    searchForm?.addEventListener('submit', (e) => {
        e.preventDefault();
        const query = document.getElementById('searchInput').value.trim();
        if (query) {
            currentQuery = query;
            currentPage = 1;
            Utils.setQueryParam('q', query);
            performSearch();
        }
    });
    
    // Clear button
    document.getElementById('clearBtn')?.addEventListener('click', () => {
        const input = document.getElementById('searchInput');
        input.value = '';
        input.focus();
    });
    
    // Tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabType = tab.dataset.tab;
            if (tabType) handleTabChange(tabType);
        });
    });
    
    // Filters
    document.getElementById('applyFilters')?.addEventListener('click', applyFilters);
    document.getElementById('clearFilters')?.addEventListener('click', clearFilters);
    
    // Pagination
    document.getElementById('prevPage')?.addEventListener('click', () => changePage(-1));
    document.getElementById('nextPage')?.addEventListener('click', () => changePage(1));
    
    // Settings
    const settingsBtn = document.getElementById('settingsBtn');
    const settingsModal = document.getElementById('settingsModal');
    const closeSettings = document.getElementById('closeSettings');
    
    settingsBtn?.addEventListener('click', () => settingsModal?.classList.remove('hidden'));
    closeSettings?.addEventListener('click', () => settingsModal?.classList.add('hidden'));
    settingsModal?.addEventListener('click', (e) => {
        if (e.target === settingsModal) settingsModal.classList.add('hidden');
    });
}

async function performSearch() {
    if (!currentQuery) return;
    
    Utils.showLoading();
    
    try {
        const params = {
            q: currentQuery,
            max_results: 10,
            ...currentFilters
        };
        
        const response = await API.search(params);
        displayResults(response.data);
        
    } catch (error) {
        Utils.showToast('Search failed', 'error');
        displayError();
    } finally {
        Utils.hideLoading();
    }
}
const RESULTS_PER_PAGE = 10;
const MAX_PAGES = 5;
const TOTAL_MAX_RESULTS = RESULTS_PER_PAGE * MAX_PAGES; // 50

async function fetchResults(query, mode, pageNumber) {
    // Calculate the offset based on the requested page number
    const offset = (pageNumber - 1) * RESULTS_PER_PAGE;

    const apiUrl = `/api/search?q=${encodeURIComponent(query)}&mode=${mode}&limit=${RESULTS_PER_PAGE}&offset=${offset}`;


    const response = await fetch(apiUrl);
    const data = await response.json();
    
    // Now the data object contains up to 10 results for the specific page.
    displayResults(data.data.results);
    renderPagination(data.data.total, pageNumber);
}

function displayResults(data) {
    // Defensive checks: ensure we have a valid results object
    try {
        if (!data || typeof data !== 'object') {
            console.error('displayResults: invalid data', data);
            displayError();
            return;
        }
    } catch (e) {
        console.error('displayResults: unexpected error validating data', e);
        displayError();
        return;
    }
    // Update search info
    const searchInfo = document.getElementById('searchInfo');
    const resultCount = data.total || 0;
    const responseTime = data.metadata?.response_time || 0;
    searchInfo.innerHTML = `
        <span class="results-count">
            About ${Utils.formatNumber(resultCount)} results (${responseTime.toFixed(2)} seconds)
        </span>
    `;
    
    // Display answer box if available
    if (data.answer_box) {
        const answerBox = document.getElementById('answerBox');
        answerBox.classList.remove('hidden');
        answerBox.querySelector('.answer-title').textContent = data.answer_box.title || '';
        answerBox.querySelector('.answer-text').textContent = data.answer_box.answer || data.answer_box.snippet || '';
        const link = answerBox.querySelector('.answer-link');
        if (data.answer_box.link) {
            link.href = data.answer_box.link;
            link.textContent = Utils.extractDomain(data.answer_box.link);
        }
    }
    
    // Display knowledge graph if available
    if (data.knowledge_graph) {
        const kg = document.getElementById('knowledgeGraph');
        kg.classList.remove('hidden');
        const kgData = data.knowledge_graph;
        if (kgData.image) kg.querySelector('.kg-image').src = kgData.image;
        kg.querySelector('.kg-title').textContent = kgData.title || '';
        kg.querySelector('.kg-type').textContent = kgData.type || '';
        kg.querySelector('.kg-description').textContent = kgData.description || '';
        const website = kg.querySelector('.kg-website');
        if (kgData.website) {
            website.href = kgData.website;
            website.textContent = kgData.website;
        }
    }
    
    // Display results
    const resultsList = document.getElementById('resultsList');
    resultsList.innerHTML = '';
    
    if (Array.isArray(data.results) && data.results.length > 0) {
        data.results.forEach(result => {
            resultsList.appendChild(createResultItem(result));
        });
    } else {
        resultsList.innerHTML = '<div class="no-results">No results found</div>';
    }
    
    // Display related searches
    if (data.related_searches && data.related_searches.length > 0) {
        const relatedList = document.querySelector('.related-list');
        relatedList.innerHTML = '';
        data.related_searches.forEach(query => {
            const item = document.createElement('div');
            item.className = 'related-item';
            item.textContent = query;
            item.onclick = () => {
                document.getElementById('searchInput').value = query;
                currentQuery = query;
                performSearch();
            };
            relatedList.appendChild(item);
        });
        document.getElementById('relatedSearches').classList.remove('hidden');
    }
}

function createResultItem(result) {
    const item = document.createElement('div');
    item.className = 'result-item';
    
    const favicon = Utils.getFaviconUrl(result.url);
    const domain = Utils.extractDomain(result.url);
    const source = result.source || 'web';
    
    item.innerHTML = `
        <div class="result-header">
            ${favicon ? `<img src="${favicon}" class="result-favicon" alt="">` : ''}
            <span class="result-domain">${domain}</span>
            <span class="result-badge badge-${source === 'local' ? 'local' : 'web'}">${source}</span>
        </div>
        <h3 class="result-title">
            <a href="${result.url}" target="_blank">${result.title}</a>
        </h3>
        <div class="result-url">${result.url}</div>
        <p class="result-snippet">${Utils.highlightText(result.snippet || '', currentQuery)}</p>
        ${result.date ? `<div class="result-meta"><span>${Utils.formatRelativeTime(result.date)}</span></div>` : ''}
    `;
    
    return item;
}

function displayError() {
    document.getElementById('resultsList').innerHTML = `
        <div class="error-message">
            <i class="fas fa-exclamation-circle"></i>
            <p>Something went wrong. Please try again.</p>
        </div>
    `;
}

function handleTabChange(tabType) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-tab="${tabType}"]`)?.classList.add('active');
    
    if (tabType === 'news') {
        loadNews();
    } else if (tabType === 'images') {
        loadImages();
    } else {
        performSearch();
    }
}

async function loadNews() {
    Utils.showLoading();
    try {
        const response = await API.searchNews(currentQuery);
        // Display news results (implement similar to displayResults)
        Utils.showToast('News search completed', 'success');
    } catch (error) {
        Utils.showToast('News search failed', 'error');
    } finally {
        Utils.hideLoading();
    }
}

async function loadImages() {
    Utils.showLoading();
    try {
        const response = await API.searchImages(currentQuery);
        // Display image results (implement grid layout)
        Utils.showToast('Image search completed', 'success');
    } catch (error) {
        Utils.showToast('Image search failed', 'error');
    } finally {
        Utils.hideLoading();
    }
}

function applyFilters() {
    const timeFilter = document.getElementById('timeFilter')?.value;
    const localOnly = document.getElementById('localOnly')?.checked;
    const webOnly = document.getElementById('webOnly')?.checked;
    
    currentFilters = {};
    if (timeFilter) currentFilters.time_period = timeFilter;
    if (localOnly) currentFilters.mode = 'local';
    if (webOnly) currentFilters.mode = 'serpapi';
    
    currentPage = 1;
    performSearch();
}

function clearFilters() {
    currentFilters = {};
    document.getElementById('timeFilter').value = '';
    document.getElementById('localOnly').checked = false;
    document.getElementById('webOnly').checked = false;
    performSearch();
}

function changePage(direction) {
    currentPage += direction;
    if (currentPage < 1) currentPage = 1;
    performSearch();
}