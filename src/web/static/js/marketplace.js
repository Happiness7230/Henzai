/**
 * Marketplace Page Logic
 * Handles product search, comparison, and price alerts
 */

let currentQuery = '';
let currentMarketplace = 'all';
let currentSort = 'relevance';
let priceFilters = { min: null, max: null };
let compareList = [];
let selectedProduct = null;

document.addEventListener('DOMContentLoaded', () => {
    currentQuery = Utils.getQueryParam('q') || '';
    if (currentQuery) {
        document.getElementById('searchInput').value = currentQuery;
        performMarketplaceSearch();
    }
    
    setupEventListeners();
});

function setupEventListeners() {
    // Search form
    document.getElementById('marketplaceSearchForm')?.addEventListener('submit', (e) => {
        e.preventDefault();
        currentQuery = document.getElementById('searchInput').value.trim();
        if (currentQuery) {
            Utils.setQueryParam('q', currentQuery);
            performMarketplaceSearch();
        }
    });
    
    // Marketplace tabs
    document.querySelectorAll('.marketplace-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.marketplace-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentMarketplace = tab.dataset.marketplace;
            performMarketplaceSearch();
        });
    });
    
    // Sort
    document.getElementById('sortBy')?.addEventListener('change', (e) => {
        currentSort = e.target.value;
        performMarketplaceSearch();
    });
    
    // Price filter modal
    document.getElementById('priceFilterBtn')?.addEventListener('click', () => {
        document.getElementById('priceFilterModal').classList.remove('hidden');
    });
    
    document.getElementById('closePriceFilter')?.addEventListener('click', () => {
        document.getElementById('priceFilterModal').classList.add('hidden');
    });
    
    document.getElementById('applyPriceFilter')?.addEventListener('click', () => {
        priceFilters.min = parseFloat(document.getElementById('minPrice').value) || null;
        priceFilters.max = parseFloat(document.getElementById('maxPrice').value) || null;
        document.getElementById('priceFilterModal').classList.add('hidden');
        performMarketplaceSearch();
    });
    
    // Compare panel
    document.getElementById('compareBtn')?.addEventListener('click', () => {
        document.getElementById('comparisonPanel').classList.toggle('hidden');
    });
    
    document.getElementById('closeComparePanel')?.addEventListener('click', () => {
        document.getElementById('comparisonPanel').classList.add('hidden');
    });
    
    document.getElementById('viewComparisonBtn')?.addEventListener('click', () => {
        viewComparison();
    });
    
    document.getElementById('clearCompareBtn')?.addEventListener('click', () => {
        clearCompareList();
    });
    
    // Alert modal
    document.getElementById('closeAlertModal')?.addEventListener('click', () => {
        document.getElementById('priceAlertModal').classList.add('hidden');
    });
    
    document.getElementById('createAlertBtn')?.addEventListener('click', () => {
        createPriceAlert();
    });
}

async function performMarketplaceSearch() {
    if (!currentQuery) return;
    
    Utils.showLoading();
    
    try {
        const params = {
            q: currentQuery,
            max_results: 20,
            sort_by: currentSort
        };
        
        if (currentMarketplace !== 'all') {
            params.marketplaces = currentMarketplace;
        }
        
        if (priceFilters.min) params.min_price = priceFilters.min;
        if (priceFilters.max) params.max_price = priceFilters.max;
        
        const response = await fetch('/api/marketplace/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            displayProducts(data.data.products);
        } else {
            Utils.showToast('Search failed: ' + data.error, 'error');
        }
        
    } catch (error) {
        Utils.showToast('Search failed', 'error');
        console.error('Marketplace search error:', error);
    } finally {
        Utils.hideLoading();
    }
}

function displayProducts(products) {
    const grid = document.getElementById('productsGrid');
    const resultsInfo = document.getElementById('resultsInfo');
    
    if (!products || products.length === 0) {
        grid.innerHTML = `
            <div class="no-results">
                <i class="fas fa-shopping-bag"></i>
                <p>No products found</p>
            </div>
        `;
        resultsInfo.textContent = '0 products found';
        return;
    }
    
    resultsInfo.textContent = `${products.length} products found`;
    
    grid.innerHTML = '';
    products.forEach(product => {
        grid.appendChild(createProductCard(product));
    });
}

function createProductCard(product) {
    const card = document.createElement('div');
    card.className = 'product-card';
    
    const isCompared = compareList.some(p => p.id === product.id);
    const marketplaceIcon = getMarketplaceIcon(product.marketplace);
    
    card.innerHTML = `
        <div class="product-image">
            <img src="${product.image || '/static/images/placeholder.png'}" 
                 alt="${product.title}" 
                 onerror="this.src='/static/images/placeholder.png'">
            <div class="product-marketplace">
                ${marketplaceIcon}
            </div>
        </div>
        
        <div class="product-info">
            <h3 class="product-title">${product.title}</h3>
            
            <div class="product-price">
                <span class="price">${formatPrice(product.price, product.currency)}</span>
                ${product.shipping_cost > 0 ? 
                    `<span class="shipping">+$${product.shipping_cost.toFixed(2)} shipping</span>` : 
                    '<span class="shipping free">Free shipping</span>'}
            </div>
            
            ${product.rating ? `
                <div class="product-rating">
                    ${'⭐'.repeat(Math.round(product.rating))}
                    <span>(${product.reviews || 0} reviews)</span>
                </div>
            ` : ''}
            
            ${!product.in_stock ? '<div class="out-of-stock">Out of Stock</div>' : ''}
            
            <div class="product-actions">
                <a href="${product.url}" target="_blank" class="btn btn-primary btn-sm">
                    View Deal
                </a>
                <button class="btn-icon" onclick="addToCompare('${product.id}', '${product.marketplace}')" 
                        title="Add to compare" ${isCompared ? 'disabled' : ''}>
                    <i class="fas fa-balance-scale"></i>
                </button>
                <button class="btn-icon" onclick="showPriceAlert('${encodeURIComponent(JSON.stringify(product))}')" 
                        title="Set price alert">
                    <i class="fas fa-bell"></i>
                </button>
            </div>
        </div>
    `;
    
    return card;
}

function formatPrice(price, currency = 'USD') {
    if (!price) return 'Price not available';
    const symbol = currency === 'USD' ? '$' : currency;
    return `${symbol}${price.toFixed(2)}`;
}

function getMarketplaceIcon(marketplace) {
    const icons = {
        'amazon': '<i class="fab fa-amazon"></i> Amazon',
        'ebay': '<i class="fas fa-gavel"></i> eBay',
        'walmart': '<i class="fas fa-store"></i> Walmart'
    };
    return icons[marketplace] || marketplace;
}

function addToCompare(productId, marketplace) {
    if (compareList.length >= 4) {
        Utils.showToast('Maximum 4 products for comparison', 'warning');
        return;
    }
    
    compareList.push({ id: productId, marketplace: marketplace });
    updateComparePanel();
    Utils.showToast('Added to comparison', 'success');
}

function removeFromCompare(productId) {
    compareList = compareList.filter(p => p.id !== productId);
    updateComparePanel();
    
    // Re-render products to update button states
    performMarketplaceSearch();
}

function updateComparePanel() {
    const count = compareList.length;
    document.getElementById('compareCount').textContent = count;
    document.getElementById('compareCountText').textContent = count;
    
    const compareItems = document.getElementById('compareItems');
    compareItems.innerHTML = '';
    
    compareList.forEach(item => {
        const div = document.createElement('div');
        div.className = 'compare-item';
        div.innerHTML = `
            <span>${item.marketplace} - ${item.id.substr(0, 10)}...</span>
            <button onclick="removeFromCompare('${item.id}')">
                <i class="fas fa-times"></i>
            </button>
        `;
        compareItems.appendChild(div);
    });
    
    document.getElementById('viewComparisonBtn').disabled = count < 2;
}

function clearCompareList() {
    compareList = [];
    updateComparePanel();
    performMarketplaceSearch();
}

async function viewComparison() {
    if (compareList.length < 2) {
        Utils.showToast('Select at least 2 products to compare', 'warning');
        return;
    }
    
    Utils.showLoading();
    
    try {
        const response = await fetch('/api/marketplace/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_ids: compareList })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            displayComparison(data.data);
        } else {
            Utils.showToast('Comparison failed', 'error');
        }
        
    } catch (error) {
        Utils.showToast('Comparison failed', 'error');
        console.error('Comparison error:', error);
    } finally {
        Utils.hideLoading();
    }
}

function displayComparison(comparisonData) {
    // Create comparison modal
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = 'comparisonModal';
    
    const products = comparisonData.products || [];
    const bestValue = comparisonData.best_value;
    
    let tableHTML = `
        <div class="modal-content comparison-modal">
            <div class="modal-header">
                <h2>Product Comparison</h2>
                <button class="close-btn" onclick="document.getElementById('comparisonModal').remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="comparison-table-wrapper">
                    <table class="comparison-table">
                        <thead>
                            <tr>
                                <th>Feature</th>
                                ${products.map((p, i) => `
                                    <th>
                                        ${bestValue && bestValue.id === p.id ? '🏆 ' : ''}
                                        Product ${i + 1}
                                    </th>
                                `).join('')}
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><strong>Title</strong></td>
                                ${products.map(p => `<td>${p.title || 'N/A'}</td>`).join('')}
                            </tr>
                            <tr>
                                <td><strong>Price</strong></td>
                                ${products.map(p => `<td class="price-cell">${formatPrice(p.price)}</td>`).join('')}
                            </tr>
                            <tr>
                                <td><strong>Marketplace</strong></td>
                                ${products.map(p => `<td>${getMarketplaceIcon(p.marketplace)}</td>`).join('')}
                            </tr>
                            <tr>
                                <td><strong>Rating</strong></td>
                                ${products.map(p => `<td>${p.rating ? '⭐'.repeat(Math.round(p.rating)) : 'N/A'}</td>`).join('')}
                            </tr>
                            <tr>
                                <td><strong>Reviews</strong></td>
                                ${products.map(p => `<td>${p.reviews || 'N/A'}</td>`).join('')}
                            </tr>
                            <tr>
                                <td><strong>Availability</strong></td>
                                ${products.map(p => `<td>${p.in_stock ? '✓ In Stock' : '✗ Out of Stock'}</td>`).join('')}
                            </tr>
                            <tr>
                                <td></td>
                                ${products.map(p => `
                                    <td>
                                        <a href="${p.url}" target="_blank" class="btn btn-primary btn-sm">
                                            View Product
                                        </a>
                                    </td>
                                `).join('')}
                            </tr>
                        </tbody>
                    </table>
                </div>
                ${bestValue ? `
                    <div class="best-value-banner">
                        <i class="fas fa-trophy"></i>
                        <span>Best Value: ${bestValue.title} at ${formatPrice(bestValue.price)}</span>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
    
    modal.innerHTML = tableHTML;
    document.body.appendChild(modal);
}

function showPriceAlert(productJson) {
    selectedProduct = JSON.parse(decodeURIComponent(productJson));
    
    const modal = document.getElementById('priceAlertModal');
    const productInfo = document.getElementById('alertProductInfo');
    const currentPriceText = document.getElementById('currentPriceText');
    
    productInfo.innerHTML = `
        <div class="alert-product">
            <img src="${selectedProduct.image}" alt="${selectedProduct.title}">
            <div>
                <h4>${selectedProduct.title}</h4>
                <p>${getMarketplaceIcon(selectedProduct.marketplace)}</p>
            </div>
        </div>
    `;
    
    currentPriceText.textContent = `Current price: ${formatPrice(selectedProduct.price)}`;
    document.getElementById('targetPrice').value = '';
    
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
        Utils.showToast('Target price should be lower than current price', 'warning');
        return;
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
                current_price: selectedProduct.price
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            Utils.showToast('Price alert created! You\'ll receive an email when the price drops.', 'success', 5000);
            document.getElementById('priceAlertModal').classList.add('hidden');
        } else {
            Utils.showToast('Failed to create alert: ' + data.error, 'error');
        }
        
    } catch (error) {
        Utils.showToast('Failed to create alert', 'error');
        console.error('Alert creation error:', error);
    } finally {
        Utils.hideLoading();
    }
}

// Make functions globally accessible
window.addToCompare = addToCompare;
window.removeFromCompare = removeFromCompare;
window.showPriceAlert = showPriceAlert;