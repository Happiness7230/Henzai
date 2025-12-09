"""
Marketplace Search Client
Aggregates product search across multiple marketplaces
"""

import os
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class MarketplaceClient:
    """
    Unified client for searching multiple marketplaces.
    Supports Amazon, eBay, Walmart, and more.
    """
    
    def __init__(self):
        """Initialize marketplace client with API credentials"""
        # Amazon credentials
        self.amazon_access_key = os.getenv('AMAZON_ACCESS_KEY')
        self.amazon_secret_key = os.getenv('AMAZON_SECRET_KEY')
        self.amazon_partner_tag = os.getenv('AMAZON_PARTNER_TAG')
        
        # eBay credentials
        self.ebay_app_id = os.getenv('EBAY_APP_ID')
        
        # RapidAPI key (for multiple marketplaces)
        self.rapidapi_key = os.getenv('RAPIDAPI_KEY')
        
        # Statistics
        self.stats = {
            'total_searches': 0,
            'amazon_searches': 0,
            'ebay_searches': 0,
            'walmart_searches': 0,
            'successful_searches': 0,
            'failed_searches': 0
        }
        
        logger.info("Marketplace client initialized")
    
    def search_all(
        self,
        query: str,
        max_results: int = 10,
        marketplaces: Optional[List[str]] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort_by: str = 'relevance'
    ) -> Dict[str, Any]:
        """
        Search across multiple marketplaces simultaneously.
        
        Args:
            query: Product search query
            max_results: Max results per marketplace
            marketplaces: List of marketplaces to search (default: all)
            min_price: Minimum price filter
            max_price: Maximum price filter
            sort_by: Sort order (relevance, price_asc, price_desc, rating)
            
        Returns:
            Aggregated results from all marketplaces
        """
        self.stats['total_searches'] += 1
        
        if not marketplaces:
            # Default marketplaces set
            marketplaces = ['amazon', 'ebay', 'walmart']

        # Filter marketplaces by available credentials and record unavailable ones
        available = []
        unavailable = []
        for m in marketplaces:
            if m == 'amazon' and self.amazon_access_key:
                available.append('amazon')
            elif m == 'ebay' and self.ebay_app_id:
                available.append('ebay')
            elif m == 'walmart' and self.rapidapi_key:
                available.append('walmart')
            else:
                unavailable.append(m)

        if not available:
            # No marketplace credentials available -> fallback to mock data
            logger.warning("No marketplace API credentials available for requested marketplaces: %s. Using mock data.", unavailable)
            mock_res = self._get_mock_marketplace_results(query, max_results, min_price, max_price)
            # Ensure metadata includes unavailable list for consistency
            if 'metadata' not in mock_res:
                mock_res['metadata'] = {}
            mock_res['metadata']['unavailable'] = unavailable
            return mock_res

        # Use only available marketplaces
        marketplaces = available
        
        results = {
            'query': query,
            'products': [],
            'results': [],  # Alias for frontend compatibility
            'marketplaces': {},
            'metadata': {
                'total_results': 0,
                'sources': [],
                'unavailable': unavailable if unavailable else [],
                'timestamp': datetime.now().isoformat()
            }
        }
        
        # Search marketplaces in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            
            if 'amazon' in marketplaces and self.amazon_access_key:
                futures['amazon'] = executor.submit(
                    self._search_amazon, query, max_results, min_price, max_price
                )
            
            if 'ebay' in marketplaces and self.ebay_app_id:
                futures['ebay'] = executor.submit(
                    self._search_ebay, query, max_results, min_price, max_price
                )
            
            if 'walmart' in marketplaces and self.rapidapi_key:
                futures['walmart'] = executor.submit(
                    self._search_walmart, query, max_results, min_price, max_price
                )
            
            # Collect results
            for marketplace, future in futures.items():
                try:
                    marketplace_results = future.result(timeout=10)
                    results['marketplaces'][marketplace] = marketplace_results
                    results['products'].extend(marketplace_results)
                    results['metadata']['sources'].append(marketplace)
                    self.stats['successful_searches'] += 1
                except Exception as e:
                    logger.error(f"{marketplace} search failed: {str(e)}")
                    results['marketplaces'][marketplace] = []
                    self.stats['failed_searches'] += 1
        
        # If we got no results from any provider, fall back to mock data
        if len(results['products']) == 0:
            logger.warning(f"No real results from any marketplace for query '{query}'. Using mock data as fallback.")
            mock_res = self._get_mock_marketplace_results(query, max_results, min_price, max_price)
            if 'metadata' not in mock_res:
                mock_res['metadata'] = {}
            mock_res['metadata']['unavailable'] = unavailable
            return mock_res
        
        # Sort and deduplicate
        results['products'] = self._deduplicate_products(results['products'])
        results['products'] = self._sort_products(results['products'], sort_by)
        results['results'] = results['products']  # Alias for frontend
        results['metadata']['total_results'] = len(results['products'])
        
        return results
    
    def _search_amazon(
        self,
        query: str,
        max_results: int,
        min_price: Optional[float],
        max_price: Optional[float]
    ) -> List[Dict]:
        """Search Amazon using Product Advertising API"""
        self.stats['amazon_searches'] += 1
        
        try:
            from amazon.paapi import AmazonAPI
            
            # Initialize Amazon API
            amazon = AmazonAPI(
                self.amazon_access_key,
                self.amazon_secret_key,
                self.amazon_partner_tag,
                country='US'
            )
            
            # Search products
            products = amazon.search_items(
                keywords=query,
                item_count=max_results
            )
            
            results = []
            for product in products.items:
                # Apply price filters
                price = self._extract_price(product.offers.listings[0].price.amount)
                if min_price and price < min_price:
                    continue
                if max_price and price > max_price:
                    continue
                
                results.append({
                    'id': product.asin,
                    'title': product.item_info.title.display_value,
                    'price': price,
                    'currency': product.offers.listings[0].price.currency,
                    'url': product.detail_page_url,
                    'image': product.images.primary.large.url if product.images else None,
                    'rating': product.item_info.rating.value if hasattr(product.item_info, 'rating') else None,
                    'reviews': product.item_info.rating.count if hasattr(product.item_info, 'rating') else None,
                    'marketplace': 'amazon',
                    'in_stock': True,
                    'timestamp': datetime.now().isoformat()
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Amazon search error: {str(e)}")
            return []
    
    def _search_ebay(
        self,
        query: str,
        max_results: int,
        min_price: Optional[float],
        max_price: Optional[float]
    ) -> List[Dict]:
        """Search eBay using Finding API"""
        self.stats['ebay_searches'] += 1
        
        try:
            from ebaysdk.finding import Connection as Finding
            
            api = Finding(appid=self.ebay_app_id, config_file=None)
            
            # Build search parameters
            params = {
                'keywords': query,
                'itemFilter': []
            }
            
            if min_price:
                params['itemFilter'].append({
                    'name': 'MinPrice',
                    'value': min_price,
                    'paramName': 'Currency',
                    'paramValue': 'USD'
                })
            
            if max_price:
                params['itemFilter'].append({
                    'name': 'MaxPrice',
                    'value': max_price,
                    'paramName': 'Currency',
                    'paramValue': 'USD'
                })
            
            # Execute search
            response = api.execute('findItemsAdvanced', params)
            items = response.dict()['searchResult']['item'][:max_results]
            
            results = []
            for item in items:
                results.append({
                    'id': item['itemId'],
                    'title': item['title'],
                    'price': float(item['sellingStatus']['currentPrice']['value']),
                    'currency': item['sellingStatus']['currentPrice']['_currencyId'],
                    'url': item['viewItemURL'],
                    'image': item.get('galleryURL'),
                    'condition': item.get('condition', {}).get('conditionDisplayName', 'Unknown'),
                    'marketplace': 'ebay',
                    'shipping_cost': float(item.get('shippingInfo', {}).get('shippingServiceCost', {}).get('value', 0)),
                    'in_stock': True,
                    'timestamp': datetime.now().isoformat()
                })
            
            return results
            
        except Exception as e:
            logger.error(f"eBay search error: {str(e)}")
            return []
    
    def _search_walmart(
        self,
        query: str,
        max_results: int,
        min_price: Optional[float],
        max_price: Optional[float]
    ) -> List[Dict]:
        """Search Walmart using RapidAPI"""
        self.stats['walmart_searches'] += 1
        
        try:

            # Assuming the new working endpoint on RapidAPI is called 'walmart-v2'
            url = "https://walmart-v2.p.rapidapi.com/items/search"
            
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "walmart-v2.p.rapidapi.com"
            }
            
            params = {
                "query": query,
                "num": max_results
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            items = data.get('items', [])
            
            results = []
            for item in items:
                price = self._extract_price(item.get('price', 0))
                
                # Apply price filters
                if min_price and price < min_price:
                    continue
                if max_price and price > max_price:
                    continue
                
                results.append({
                    'id': item.get('usItemId', ''),
                    'title': item.get('name', ''),
                    'price': price,
                    'currency': 'USD',
                    'url': item.get('productPageUrl', ''),
                    'image': item.get('thumbnailUrl', ''),
                    'rating': item.get('rating', {}).get('averageRating'),
                    'reviews': item.get('rating', {}).get('numberOfReviews'),
                    'marketplace': 'walmart',
                    'in_stock': item.get('availabilityStatus') == 'IN_STOCK',
                    'timestamp': datetime.now().isoformat()
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Walmart search error: {str(e)}")
            return []
    
    def compare_products(self, product_ids: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Compare multiple products side-by-side.
        
        Args:
            product_ids: List of dicts with 'id' and 'marketplace'
            
        Returns:
            Comparison data
        """
        products = []
        
        for item in product_ids:
            product_id = item['id']
            marketplace = item['marketplace']
            
            # Fetch detailed product info
            if marketplace == 'amazon':
                product = self._get_amazon_product(product_id)
            elif marketplace == 'ebay':
                product = self._get_ebay_product(product_id)
            elif marketplace == 'walmart':
                product = self._get_walmart_product(product_id)
            else:
                continue
            
            if product:
                products.append(product)
        
        return {
            'products': products,
            'comparison_matrix': self._build_comparison_matrix(products),
            'best_value': self._find_best_value(products),
            'timestamp': datetime.now().isoformat()
        }
    
    def _build_comparison_matrix(self, products: List[Dict]) -> Dict:
        """Build feature comparison matrix"""
        if not products:
            return {}
        
        # Extract common features
        features = {}
        for product in products:
            features['price'] = features.get('price', []) + [product.get('price')]
            features['rating'] = features.get('rating', []) + [product.get('rating')]
            features['reviews'] = features.get('reviews', []) + [product.get('reviews')]
            features['marketplace'] = features.get('marketplace', []) + [product.get('marketplace')]
        
        return features
    
    def _find_best_value(self, products: List[Dict]) -> Optional[Dict]:
        """Find best value product based on price and rating"""
        if not products:
            return None
        
        # Simple scoring: (rating / price) * 100
        best_product = None
        best_score = 0
        
        for product in products:
            price = product.get('price', 0)
            rating = product.get('rating', 0)
            
            if price > 0 and rating > 0:
                score = (rating / price) * 100
                if score > best_score:
                    best_score = score
                    best_product = product
        
        return best_product
    
    def _deduplicate_products(self, products: List[Dict]) -> List[Dict]:
        """Remove duplicate products based on title similarity"""
        if not products:
            return []
        
        unique_products = []
        seen_titles = set()
        
        for product in products:
            # Normalize title
            title = product.get('title', '').lower().strip()
            title_key = ''.join(title.split()[:5])  # First 5 words
            
            if title_key not in seen_titles:
                unique_products.append(product)
                seen_titles.add(title_key)
        
        return unique_products
    
    def _sort_products(self, products: List[Dict], sort_by: str) -> List[Dict]:
        """Sort products by specified criteria"""
        if not products:
            return []
        
        if sort_by == 'price_asc':
            return sorted(products, key=lambda x: x.get('price', float('inf')))
        elif sort_by == 'price_desc':
            return sorted(products, key=lambda x: x.get('price', 0), reverse=True)
        elif sort_by == 'rating':
            return sorted(products, key=lambda x: x.get('rating', 0), reverse=True)
        else:  # relevance (default order)
            return products
    
    @staticmethod
    def _extract_price(price_value: Any) -> float:
        """Extract numeric price from various formats"""
        try:
            if isinstance(price_value, (int, float)):
                return float(price_value)
            if isinstance(price_value, str):
                # Remove currency symbols and convert
                price_str = price_value.replace('$', '').replace(',', '').strip()
                return float(price_str)
            return 0.0
        except:
            return 0.0
    
    def _get_mock_marketplace_results(
        self,
        query: str,
        max_results: int,
        min_price: Optional[float],
        max_price: Optional[float]
    ) -> Dict[str, Any]:
        """Return mock marketplace results for demo/testing"""
        mock_products = [
            {
                'id': 'mock-1',
                'title': f'{query} - Premium Edition',
                'price': 99.99,
                'currency': 'USD',
                'url': 'https://example.com/product1',
                'image': 'https://via.placeholder.com/200?text=Product+1',
                'rating': 4.5,
                'reviews': 128,
                'marketplace': 'amazon',
                'in_stock': True,
                'shipping': 'Free shipping',
                'timestamp': datetime.now().isoformat()
            },
            {
                'id': 'mock-2',
                'title': f'{query} - Standard Edition',
                'price': 49.99,
                'currency': 'USD',
                'url': 'https://example.com/product2',
                'image': 'https://via.placeholder.com/200?text=Product+2',
                'rating': 4.2,
                'reviews': 89,
                'marketplace': 'ebay',
                'in_stock': True,
                'shipping': '$5.00 shipping',
                'timestamp': datetime.now().isoformat()
            },
            {
                'id': 'mock-3',
                'title': f'{query} - Deluxe Package',
                'price': 149.99,
                'currency': 'USD',
                'url': 'https://example.com/product3',
                'image': 'https://via.placeholder.com/200?text=Product+3',
                'rating': 4.7,
                'reviews': 256,
                'marketplace': 'walmart',
                'in_stock': True,
                'shipping': 'Free shipping',
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        # Apply price filters
        filtered = mock_products
        if min_price:
            filtered = [p for p in filtered if p['price'] >= min_price]
        if max_price:
            filtered = [p for p in filtered if p['price'] <= max_price]
        
        filtered = filtered[:max_results]
        
        return {
            'query': query,
            'products': filtered,
            'results': filtered,
            'marketplaces': {'demo': filtered},
            'metadata': {
                'total_results': len(filtered),
                'sources': ['demo'],
                'timestamp': datetime.now().isoformat(),
                'note': 'Mock data - configure API credentials for real results'
            }
        }
    
    def _get_amazon_product(self, product_id: str) -> Optional[Dict]:
        """Get detailed Amazon product info"""
        # Implementation for fetching single product
        pass
    
    def _get_ebay_product(self, product_id: str) -> Optional[Dict]:
        """Get detailed eBay product info"""
        pass
    
    def _get_walmart_product(self, product_id: str) -> Optional[Dict]:
        """Get detailed Walmart product info"""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get marketplace client statistics"""
        return {
            **self.stats,
            'success_rate': (
                self.stats['successful_searches'] / self.stats['total_searches'] * 100
                if self.stats['total_searches'] > 0 else 0
            )
        }