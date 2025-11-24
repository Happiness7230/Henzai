/**
 * Marketplace Page Logic
 * Handles product search, comparison, and price alerts
 */

let currentQuery = '';
let currentMarketplace = 'all';
let currentSort = 'relevance';
let priceFilters = { min: null, max: null };
let compareList = [];
let allProducts = [];
let selectedProduct = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Get query from URL parameter
    currentQuery = Utils.getQueryParam('q') || '';
    if (currentQuery) {
        document.getElementById('searchInput').value = currentQuery;
        performMarketplaceSearch();
    }
    
    setupEventListeners();
    
    // Check for saved dark mode preference
    if (localStorage.getItem('darkMode') === 'enabled') {
        document.body.classList.add('dark-mode');
        const icon = document.querySelector('#darkModeBtn i');
        if (icon) {
            icon.classList.replace('fa-moon', 'fa-sun');
        }
    }
});

function setupEventListeners() {
    // Search form submission
    const searchForm = document.getElementById('marketplaceSearchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            currentQuery = document.getElementById('searchInput').value.trim();
            if (currentQuery) {
                Utils.setQueryParam('q', currentQuery);
                performMarketplaceSearch();
            }
        });
    }
    
    // Marketplace tabs
    document.querySelectorAll('.marketplace-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            // Update active tab
            document.querySelectorAll('.marketplace-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            currentMarketplace = tab.dataset.marketplace;
            performMarketplaceSearch();
        });
    });
    
    // Sort dropdown
    const sortBy = document.getElementById('sortBy');
    if (sortBy) {
        sortBy.addEventListener('change', (e) => {
            currentSort = e.target.value;
            performMarketplaceSearch();
        });
    }
    
    // Price filter button and modal
    const priceFilterBtn = document.getElementById('priceFilterBtn');
    const priceFilterModal = document.getElementById('priceFilterModal');
    const closePriceFilter = document.getElementById('closePriceFilter');
    const applyPriceFilter = document.getElementById('applyPriceFilter');
    
    if (priceFilterBtn) {
        priceFilterBtn.addEventListener('click', () => {
            priceFilterModal.classList.remove('hidden');
        });
    }
    
    if (closePriceFilter) {
        closePriceFilter.addEventListener('click', () => {
            priceFilterModal.classList.add('hidden');
        });
    }
    
    if (applyPriceFilter) {
        applyPriceFilter.addEventListener('click', () => {
            priceFilters.min = parseFloat(document.getElementById('minPrice').value) || null;
            priceFilters.max = parseFloat(document.getElementById('maxPrice').value) || null;
            priceFilterModal.classList.add('hidden');
            performMarketplaceSearch();
        });
    }
    
    // Compare panel controls
    const compareBtn = document.getElementById('compareBtn');
    const comparisonPanel = document.getElementById('comparisonPanel');
    const closeComparePanel = document.getElementById('closeComparePanel');
    const clearCompareBtn = document.getElementById('clearCompareBtn');
    const viewComparisonBtn = document.getElementById('viewComparisonBtn');
    
    if (compareBtn) {
        compareBtn.addEventListener('click', () => {
            comparisonPanel.classList.toggle('hidden');
        });
    }
    
    if (closeComparePanel) {
        closeComparePanel.addEventListener('click', () => {
            comparisonPanel.classList.add('hidden');
        });
    }
    
    if (clearCompareBtn) {
        clearCompareBtn.addEventListener('click', () => {
            clearCompareList();
        });
    }
    
    if (viewComparisonBtn) {
        viewComparisonBtn.addEventListener('click', () => {
            viewComparison();
        });
    }
    
    // Alert modal controls
    const closeAlertModal = document.getElementById('closeAlertModal');
    const createAlertBtn = document.getElementById('createAlertBtn');
    
    if (closeAlertModal) {
        closeAlertModal.addEventListener('click', () => {
            document.getElementById('priceAlertModal').classList.add('hidden');
        });
    }
    
    if (createAlertBtn) {
        createAlertBtn.addEventListener('click', () => {
            createPriceAlert();
        });
    }
    
    // Dark mode toggle
    const darkModeBtn = document.getElementById('darkModeBtn');
    if (darkModeBtn) {
        darkModeBtn.addEventListener('click', toggleDarkMode);
    }
    
    // Close modals on background click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.add('hidden');
            }
        });
    });
}

async function performMarketplaceSearch() {
    if (!currentQuery) {
        Utils.showToast('Please enter a search query', 'warning');
        return;
    }
    
    // Show loading state
    showLoading();
    
    try {
        // Build search parameters
        const params = {
            q: currentQuery,
            max_results: 30,
            sort_by: currentSort
        };
        
        // Add marketplace filter
        if (currentMarketplace !== 'all') {
            params.marketplaces = currentMarketplace;
        }
        
        // Add price range
        if (priceFilters.min) params.min_price = priceFilters.min;
        if (priceFilters.max) params.max_price = priceFilters.max;
        
        // Perform search using POST
        const response = await fetch('/api/marketplace/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });
        
        if (!response.ok) {
            throw new Error('HTTP ' + response.status + ': ' + response.statusText);
        }
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // Store all products
            allProducts = data.data.products || data.data.results || [];
            displayProducts(allProducts);
        } else {
            throw new Error(data.error || 'Search failed');
        }
        
    } catch (error) {
        console.error('Marketplace search error:', error);
        showError(error.message);
        Utils.showToast('Search failed: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

function showLoading() {
    const resultsInfo = document.getElementById('resultsInfo');
    const productsGrid = document.getElementById('productsGrid');
    
    if (resultsInfo) {
        resultsInfo.innerHTML = '<span>Searching...</span>';
    }
    
    if (productsGrid) {
        productsGrid.innerHTML = '<div class="skeleton-loader">' +
            '<div class="product-skeleton"></div>' +
            '<div class="product-skeleton"></div>' +
            '<div class="product-skeleton"></div>' +
            '<div class="product-skeleton"></div>' +
            '</div>';
    }
}

function hideLoading() {
    // Loading state is replaced by results
}

function displayProducts(products) {
    const grid = document.getElementById('productsGrid');
    const resultsInfo = document.getElementById('resultsInfo');
    
    if (!products || products.length === 0) {
        grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 60px;">' +
            '<i class="fas fa-shopping-bag" style="font-size: 60px; color: var(--text-secondary); margin-bottom: 20px;"></i>' +
            '<h3>No products found</h3>' +
            '<p style="color: var(--text-secondary);">Try different keywords or filters</p>' +
            '</div>';
        resultsInfo.textContent = '0 products found';
        return;
    }
    
    // Update results info
    const count = products.length;
    resultsInfo.innerHTML = '<span>Found <strong>' + count + '</strong> product' + 
        (count !== 1 ? 's' : '') + ' for "' + currentQuery + '"</span>';
    
    // Render products
    grid.innerHTML = '';
    products.forEach(product => {
        const card = createProductCard(product);
        grid.appendChild(card);
    });
}

function createProductCard(product) {
    const card = document.createElement('div');
    card.className = 'product-card';
    card.dataset.productId = product.id;
    
    const isCompared = compareList.some(p => p.id === product.id);
    const marketplaceIcon = getMarketplaceIcon(product.marketplace);
    const price = product.price || 0;
    const rating = product.rating || 0;
    const reviews = product.reviews || 0;
    const isOutOfStock = product.in_stock === false || 
                        (product.availability && product.availability.toLowerCase().includes('out of stock'));
    
    // Build star rating
    const starCount = Math.floor(rating);
    const emptyStarCount = 5 - starCount;
    let stars = '';
    for (let i = 0; i < starCount; i++) stars += '★';
    for (let i = 0; i < emptyStarCount; i++) stars += '☆';
    
    // Build product image
    let imageHtml = '';
    if (product.image_url || product.image) {
        imageHtml = '<img src="' + escapeHtml(product.image_url || product.image) + 
                   '" alt="' + escapeHtml(product.title) + 
                   '" loading="lazy" onerror="this.src=\'/static/images/placeholder.png\'">';
    } else {
        imageHtml = '<div style="width:100%; height:100%; display:flex; align-items:center; justify-content:center; background: var(--bg-secondary);">' +
                   '<i class="fas fa-image" style="font-size: 48px; color: var(--text-secondary);"></i>' +
                   '</div>';
    }
    
    // Build shipping info
    let shippingHtml = '';
    if (product.shipping_cost && product.shipping_cost > 0) {
        shippingHtml = '<span class="shipping">+$' + product.shipping_cost.toFixed(2) + ' shipping</span>';
    } else if (product.shipping && product.shipping.toLowerCase() === 'free') {
        shippingHtml = '<span class="shipping free">Free shipping</span>';
    } else if (product.shipping) {
        shippingHtml = '<span class="shipping">' + escapeHtml(product.shipping) + '</span>';
    }
    
    // Build rating HTML
    let ratingHtml = '';
    if (rating > 0) {
        ratingHtml = '<div class="product-rating">' +
            '<span style="color: #ffa000;">' + stars + '</span>' +
            '<span>' + rating.toFixed(1) + '</span>';
        if (reviews > 0) {
            ratingHtml += '<span>(' + reviews + ')</span>';
        }
        ratingHtml += '</div>';
    }
    
    card.innerHTML = '<div class="product-image">' +
        imageHtml +
        '<span class="product-marketplace">' + escapeHtml(marketplaceIcon) + '</span>' +
        '</div>' +
        '<div class="product-info">' +
        '<h3 class="product-title">' + escapeHtml(product.title || product.name || 'Product') + '</h3>' +
        '<div class="product-price">' +
        '<span class="price">' + formatPrice(price, product.currency) + '</span>' +
        shippingHtml +
        '</div>' +
        ratingHtml +
        (isOutOfStock ? '<span class="out-of-stock">Out of Stock</span>' : '') +
        '<div class="product-actions">' +
        '<button class="btn btn-primary btn-sm" onclick="window.open(\'' + product.url + '\', \'_blank\')" ' +
        (isOutOfStock ? 'disabled' : '') + '>' +
        '<i class="fas fa-external-link-alt"></i> View Deal' +
        '</button>' +
        '<button class="btn-icon ' + (isCompared ? 'active' : '') + '" ' +
        'onclick="addToCompare(\'' + product.id + '\')" title="Add to comparison" ' +
        (compareList.length >= 4 && !isCompared ? 'disabled' : '') + '>' +
        '<i class="fas fa-balance-scale"></i>' +
        '</button>' +
        '<button class="btn-icon" onclick="showPriceAlert(\'' + product.id + '\')" title="Set price alert">' +
        '<i class="fas fa-bell"></i>' +
        '</button>' +
        '</div>' +
        '</div>';
    
    return card;
}

function formatPrice(price, currency) {
    if (!price) return 'Price not available';
    currency = currency || 'USD';
    const symbol = currency === 'USD' ? '$' : currency;
    return symbol + parseFloat(price).toFixed(2);
}

function getMarketplaceIcon(marketplace) {
    const icons = {
        'amazon': '<i class="fab fa-amazon"></i> Amazon',
        'ebay': '<i class="fas fa-gavel"></i> eBay',
        'walmart': '<i class="fas fa-store"></i> Walmart'
    };
    const lowerMarketplace = (marketplace || '').toLowerCase();
    return icons[lowerMarketplace] || marketplace || 'Store';
}

function addToCompare(productId) {
    const product = allProducts.find(p => p.id === productId);
    if (!product) {
        console.error('Product not found:', productId);
        return;
    }
    
    // Check if already in compare list
    const index = compareList.findIndex(p => p.id === productId);
    
    if (index > -1) {
        // Remove from comparison
        compareList.splice(index, 1);
        Utils.showToast('Removed from comparison', 'info');
    } else {
        // Add to comparison (max 4)
        if (compareList.length >= 4) {
            Utils.showToast('Maximum 4 products for comparison', 'warning');
            return;
        }
        compareList.push(product);
        Utils.showToast('Added to comparison', 'success');
    }
    
    updateComparePanel();
    displayProducts(allProducts); // Re-render to update button states
}

function removeFromCompare(productId) {
    compareList = compareList.filter(p => p.id !== productId);
    updateComparePanel();
    displayProducts(allProducts);
    Utils.showToast('Removed from comparison', 'info');
}

function updateComparePanel() {
    const count = compareList.length;
    const compareCount = document.getElementById('compareCount');
    const compareCountText = document.getElementById('compareCountText');
    const compareItems = document.getElementById('compareItems');
    const viewComparisonBtn = document.getElementById('viewComparisonBtn');
    
    if (compareCount) compareCount.textContent = count;
    if (compareCountText) compareCountText.textContent = count;
    
    // Update compare items list
    if (compareItems) {
        compareItems.innerHTML = '';
        compareList.forEach(product => {
            const div = document.createElement('div');
            div.className = 'compare-item';
            
            const title = product.title.substring(0, 40);
            const displayTitle = product.title.length > 40 ? title + '...' : title;
            
            div.innerHTML = '<div>' +
                '<div style="font-weight: 600; font-size: 14px; margin-bottom: 4px;">' +
                escapeHtml(displayTitle) +
                '</div>' +
                '<div style="color: var(--primary-color); font-weight: 700;">' +
                formatPrice(product.price, product.currency) +
                '</div>' +
                '</div>' +
                '<button class="btn-icon" onclick="removeFromCompare(\'' + product.id + '\')" title="Remove">' +
                '<i class="fas fa-times"></i>' +
                '</button>';
            
            compareItems.appendChild(div);
        });
    }
    
    // Enable/disable comparison button
    if (viewComparisonBtn) {
        viewComparisonBtn.disabled = count < 2;
    }
}

function clearCompareList() {
    compareList = [];
    updateComparePanel();
    displayProducts(allProducts);
    Utils.showToast('Comparison list cleared', 'info');
}

function viewComparison() {
    if (compareList.length < 2) {
        Utils.showToast('Select at least 2 products to compare', 'warning');
        return;
    }
    
    displayComparison({ products: compareList });
}

function displayComparison(comparisonData) {
    const products = comparisonData.products || [];
    
    // Find best value (lowest price)
    const lowestPrice = Math.min.apply(null, products.map(p => p.price || Infinity));
    const bestValue = products.find(p => p.price === lowestPrice);
    
    // Create comparison modal
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = 'comparisonModal';
    modal.style.display = 'flex';
    
    // Build table headers
    let headerCells = '';
    products.forEach((p, i) => {
        const isBest = bestValue && bestValue.id === p.id;
        headerCells += '<th>' + (isBest ? '🏆 ' : '') + 'Product ' + (i + 1) + '</th>';
    });
    
    // Build table rows
    function buildRow(label, mapper) {
        let cells = '';
        products.forEach(p => {
            cells += '<td>' + mapper(p) + '</td>';
        });
        return '<tr><td><strong>' + label + '</strong></td>' + cells + '</tr>';
    }
    
    const titleRow = buildRow('Title', p => escapeHtml(p.title || 'N/A'));
    const priceRow = buildRow('Price', p => '<span class="price-cell">' + formatPrice(p.price, p.currency) + '</span>');
    const marketplaceRow = buildRow('Marketplace', p => getMarketplaceIcon(p.marketplace));
    
    const ratingRow = buildRow('Rating', p => {
        if (!p.rating) return 'N/A';
        const stars = Math.round(p.rating);
        let starStr = '';
        for (let i = 0; i < stars; i++) starStr += '★';
        return starStr;
    });
    
    const reviewsRow = buildRow('Reviews', p => p.reviews || 'N/A');
    const shippingRow = buildRow('Shipping', p => escapeHtml(p.shipping || 'N/A'));
    const availRow = buildRow('Availability', p => p.in_stock !== false ? '✓ In Stock' : '✗ Out of Stock');
    
    const actionRow = '<tr><td></td>' + products.map(p => 
        '<td><a href="' + p.url + '" target="_blank" class="btn btn-primary btn-sm">View Product</a></td>'
    ).join('') + '</tr>';
    
    // Best value banner
    let bannerHtml = '';
    if (bestValue) {
        const shortTitle = bestValue.title.substring(0, 50);
        const displayTitle = bestValue.title.length > 50 ? shortTitle + '...' : shortTitle;
        bannerHtml = '<div class="best-value-banner">' +
            '<i class="fas fa-trophy" style="font-size: 24px;"></i>' +
            '<div>' +
            '<div><strong>Best Value:</strong></div>' +
            '<div>' + escapeHtml(displayTitle) + ' - ' + formatPrice(bestValue.price, bestValue.currency) + '</div>' +
            '</div>' +
            '</div>';
    }
    
    modal.innerHTML = '<div class="modal-content comparison-modal">' +
        '<div class="modal-header">' +
        '<h2>Product Comparison</h2>' +
        '<button class="close-btn" onclick="document.getElementById(\'comparisonModal\').remove()">' +
        '<i class="fas fa-times"></i>' +
        '</button>' +
        '</div>' +
        '<div class="modal-body">' +
        '<div class="comparison-table-wrapper">' +
        '<table class="comparison-table">' +
        '<thead><tr><th>Feature</th>' + headerCells + '</tr></thead>' +
        '<tbody>' +
        titleRow + priceRow + marketplaceRow + ratingRow + reviewsRow + shippingRow + availRow + actionRow +
        '</tbody>' +
        '</table>' +
        '</div>' +
        bannerHtml +
        '</div>' +
        '</div>';
    
    document.body.appendChild(modal);
    
    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

function showPriceAlert(productId) {
    selectedProduct = allProducts.find(p => p.id === productId);
    
    if (!selectedProduct) {
        console.error('Product not found for alert:', productId);
        Utils.showToast('Product not found', 'error');
        return;
    }
    
    const modal = document.getElementById('priceAlertModal');
    const productInfo = document.getElementById('alertProductInfo');
    const currentPriceText = document.getElementById('currentPriceText');
    
    let imageHtml = '';
    if (selectedProduct.image_url || selectedProduct.image) {
        imageHtml = '<img src="' + escapeHtml(selectedProduct.image_url || selectedProduct.image) + 
                   '" alt="' + escapeHtml(selectedProduct.title) + '">';
    } else {
        imageHtml = '<div style="width:80px;height:80px;background:var(--bg-secondary);border-radius:8px;"></div>';
    }
    
    productInfo.innerHTML = '<div class="alert-product">' +
        imageHtml +
        '<div>' +
        '<h4>' + escapeHtml(selectedProduct.title) + '</h4>' +
        '<p>' + getMarketplaceIcon(selectedProduct.marketplace) + '</p>' +
        '</div>' +
        '</div>';
    
    currentPriceText.textContent = 'Current price: ' + formatPrice(selectedProduct.price, selectedProduct.currency);
    document.getElementById('targetPrice').value = '';
    document.getElementById('alertEmail').value = '';
    
    modal.classList.remove('hidden');
}

async function createPriceAlert() {
    const email = document.getElementById('alertEmail').value.trim();
    const targetPrice = parseFloat(document.getElementById('targetPrice').value);
    
    if (!email || !Utils.isValidEmail(email)) {
        Utils.showToast('Please enter a valid email', 'error');
        return;
    }
    
    if (!targetPrice || targetPrice <= 0) {
        Utils.showToast('Please enter a valid target price', 'error');
        return;
    }
    
    if (targetPrice >= selectedProduct.price) {
        const confirmResult = confirm('Target price is higher than or equal to current price. Do you still want to create this alert?');
        if (!confirmResult) return;
    }
    
    Utils.showLoading();
    
    try {
        const response = await fetch('/api/alerts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: email,
                product_name: selectedProduct.title,
                product_url: selectedProduct.url,
                marketplace: selectedProduct.marketplace,
                target_price: targetPrice,
                current_price: selectedProduct.price || 0
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            Utils.showToast('✓ Price alert created! You will receive an email when the price drops.', 'success', 5000);
            document.getElementById('priceAlertModal').classList.add('hidden');
            document.getElementById('alertEmail').value = '';
            document.getElementById('targetPrice').value = '';
        } else {
            Utils.showToast('Failed to create alert: ' + data.error, 'error');
        }
        
    } catch (error) {
        console.error('Alert creation error:', error);
        Utils.showToast('Failed to create alert: ' + error.message, 'error');
    } finally {
        Utils.hideLoading();
    }
}

function showError(message) {
    const resultsInfo = document.getElementById('resultsInfo');
    const productsGrid = document.getElementById('productsGrid');
    
    if (resultsInfo) {
        resultsInfo.innerHTML = '<span style="color: var(--danger-color);">Search failed</span>';
    }
    
    if (productsGrid) {
        productsGrid.innerHTML = '<div style="grid-column: 1/-1; padding: 40px; text-align: center;">' +
            '<div style="background: #ffebee; color: #c62828; padding: 20px; border-radius: 8px; border-left: 4px solid #c62828;">' +
            '<strong>Error:</strong> ' + escapeHtml(message) +
            '</div>' +
            '<p style="margin-top: 20px; color: var(--text-secondary);">' +
            'Please try again or contact support if the problem persists.' +
            '</p>' +
            '</div>';
    }
}

function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const icon = document.querySelector('#darkModeBtn i');
    
    if (document.body.classList.contains('dark-mode')) {
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
        localStorage.setItem('darkMode', 'enabled');
    } else {
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
        localStorage.setItem('darkMode', 'disabled');
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Make functions globally accessible
window.addToCompare = addToCompare;
window.removeFromCompare = removeFromCompare;
window.showPriceAlert = showPriceAlert;