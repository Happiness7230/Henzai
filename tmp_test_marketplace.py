import os
from src.marketplace.marketplace_client import MarketplaceClient

# Ensure credentials are not set in the process env for test
for k in ['AMAZON_ACCESS_KEY','AMAZON_SECRET_KEY','AMAZON_PARTNER_TAG','EBAY_APP_ID','RAPIDAPI_KEY']:
    if k in os.environ:
        del os.environ[k]

mc = MarketplaceClient()
res = mc.search_all('test-product', max_results=5)
print('keys in metadata:', list(res.get('metadata', {}).keys()))
print('unavailable:', res.get('metadata', {}).get('unavailable'))
print('total_results:', res.get('metadata', {}).get('total_results'))
print('sources:', res.get('metadata', {}).get('sources'))
print('products_count:', len(res.get('products', [])))
print('sample product:', res.get('products', [None])[0])
