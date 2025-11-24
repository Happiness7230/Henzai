"""
Setup script for Search Engine project
"""

from setuptools import setup, find_packages
import sys
import os

# Add project root to path
if __name__ == '__main__':
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    
setup(
    name="search-engine",
    version="4.0.0",
    packages=find_packages(),
    install_requires=[
        'Flask==2.3.0',
        'beautifulsoup4==4.12.0',
        'requests==2.31.0',
        'nltk==3.8.1',
        'redis==4.5.0',
        'psutil==5.9.0',
        'google-search-results==2.4.2',
        'python-dotenv==1.0.0',
        'tenacity==8.2.3',
        'ratelimit==2.2.1',
        'google-api-python-client==2.108.0',
        'ebaysdk==2.2.0',
        'amazon-paapi5==5.0.6',
        'celery==5.3.4',
        'python-crontab==3.0.0',
        'requests-cache==1.1.1',
        'flask-cors==4.0.0',
    ],
    python_requires='>=3.8',
)
