"""
Job Search Client
Aggregates job postings from multiple sources
"""

import os
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class JobSearchClient:
    """
    Unified client for searching job postings.
    Supports Indeed, LinkedIn, Glassdoor via RapidAPI
    """
    
    def __init__(self):
        """Initialize job search client"""
        self.rapidapi_key = os.getenv('RAPIDAPI_KEY')
        
        # Statistics
        self.stats = {
            'total_searches': 0,
            'successful_searches': 0,
            'failed_searches': 0,
            'total_jobs_returned': 0
        }
        
        logger.info("Job search client initialized")
    
    def search_jobs(
        self,
        query: str,
        location: str = '',
        max_results: int = 20,
        remote_only: bool = False,
        min_salary: Optional[int] = None,
        experience_level: Optional[str] = None,
        job_type: Optional[str] = None,
        sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search for jobs across multiple platforms.
        
        Args:
            query: Job search query (title, keywords)
            location: Job location
            max_results: Maximum results to return
            remote_only: Filter for remote jobs only
            min_salary: Minimum salary filter
            experience_level: Entry, Mid, Senior
            job_type: Full-time, Part-time, Contract, etc.
            sources: List of job boards to search
            
        Returns:
            Aggregated job results
        """
        self.stats['total_searches'] += 1
        
        # If no API key, always use mock data
        if not self.rapidapi_key:
            logger.warning("RapidAPI key not configured. Using mock job data.")
            return self._get_mock_job_results(query, location, max_results, remote_only, min_salary)
        
        if not sources:
            sources = ['indeed', 'linkedin']

        # Normalize job_type and experience_level when callers pass arrays (frontend may send arrays)
        if isinstance(job_type, list):
            job_type = job_type[0] if job_type else None
        if isinstance(experience_level, list):
            experience_level = experience_level[0] if experience_level else None
        
        results = {
            'query': query,
            'location': location,
            'jobs': [],
            'results': [],  # Alias for frontend compatibility
            'sources': {},
            'metadata': {
                'total_results': 0,
                'sources_searched': [],
                'timestamp': datetime.now().isoformat()
            }
        }
        
        # Search job boards in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            
            if 'indeed' in sources:
                futures['indeed'] = executor.submit(
                    self._search_indeed, query, location, max_results,
                    remote_only, min_salary, job_type
                )
            
            if 'linkedin' in sources:
                futures['linkedin'] = executor.submit(
                    self._search_linkedin, query, location, max_results,
                    remote_only, experience_level
                )
            
            if 'glassdoor' in sources:
                futures['glassdoor'] = executor.submit(
                    self._search_glassdoor, query, location, max_results
                )
            
            # Collect results
            for source, future in futures.items():
                try:
                    source_results = future.result(timeout=15)
                    results['sources'][source] = source_results
                    results['jobs'].extend(source_results)
                    results['metadata']['sources_searched'].append(source)
                    self.stats['successful_searches'] += 1
                except Exception as e:
                    logger.error(f"{source} job search failed: {str(e)}")
                    results['sources'][source] = []
                    self.stats['failed_searches'] += 1
        
        # If we got no results from any source, fall back to mock data
        if len(results['jobs']) == 0:
            logger.info("No real results found, using mock data as fallback")
            return self._get_mock_job_results(query, location, max_results, remote_only, min_salary)
        
        # Deduplicate and sort
        results['jobs'] = self._deduplicate_jobs(results['jobs'])
        results['jobs'] = self._sort_jobs(results['jobs'], min_salary)
        results['results'] = results['jobs']  # Alias for frontend
        results['metadata']['total_results'] = len(results['jobs'])
        self.stats['total_jobs_returned'] += len(results['jobs'])
        
        return results
    
    def _search_indeed(
        self,
        query: str,
        location: str,
        max_results: int,
        remote_only: bool,
        min_salary: Optional[int],
        job_type: Optional[str]
    ) -> List[Dict]:
        """Search Indeed via RapidAPI"""
        if not self.rapidapi_key:
            return []
        
        try:
            url = "https://indeed12.p.rapidapi.com/jobs/search"
            
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "indeed12.p.rapidapi.com"
            }
            
            params = {
                "query": query,
                "location": location,
                "page_id": "1",
                "locality": "us",
                "fromage": "30",  # Last 30 days
                "radius": "50"
            }
            
            if remote_only:
                params["remotejob"] = "true"
            
            if job_type:
                try:
                    params["jt"] = str(job_type).lower()
                except Exception:
                    params["jt"] = str(job_type)
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            jobs = data.get('hits', [])[:max_results]
            
            results = []
            for job in jobs:
                salary = self._parse_salary(job.get('salary', ''))
                
                # Apply salary filter
                if min_salary and salary and salary < min_salary:
                    continue
                
                results.append({
                    'id': job.get('id', ''),
                    'title': job.get('title', ''),
                    'company': job.get('company_name', ''),
                    'location': job.get('location', ''),
                    'description': job.get('description', ''),
                    'salary': salary,
                    'salary_text': job.get('salary', 'Not specified'),
                    'job_type': job.get('job_type', ''),
                    'remote': 'remote' in job.get('title', '').lower() or 
                             'remote' in job.get('location', '').lower(),
                    'posted_date': job.get('date', ''),
                    'url': job.get('link', ''),
                    'source': 'indeed',
                    'timestamp': datetime.now().isoformat()
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Indeed search error: {str(e)}")
            return []
    
    def _search_linkedin(
        self,
        query: str,
        location: str,
        max_results: int,
        remote_only: bool,
        experience_level: Optional[str]
    ) -> List[Dict]:
        """Search LinkedIn via RapidAPI"""
        if not self.rapidapi_key:
            return []
        
        try:
            url = "https://linkedin-data-api.p.rapidapi.com/search-jobs"
            
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "linkedin-data-api.p.rapidapi.com"
            }
            
            params = {
                "keywords": query,
                "locationId": location or "92000000",  # US
                "datePosted": "anyTime",
                "sort": "mostRelevant"
            }
            
            if remote_only:
                params["workplaceType"] = "remote"
            
            if experience_level:
                try:
                    params["experienceLevel"] = str(experience_level).lower()
                except Exception:
                    params["experienceLevel"] = str(experience_level)
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            jobs = data.get('data', [])[:max_results]
            
            results = []
            for job in jobs:
                results.append({
                    'id': job.get('id', ''),
                    'title': job.get('title', ''),
                    'company': job.get('company', {}).get('name', ''),
                    'location': job.get('location', ''),
                    'description': job.get('description', ''),
                    'salary': None,
                    'salary_text': 'Not specified',
                    'job_type': job.get('workplaceType', ''),
                    'remote': job.get('workplaceType', '').lower() == 'remote',
                    'posted_date': job.get('postedDate', ''),
                    'url': job.get('url', ''),
                    'source': 'linkedin',
                    'timestamp': datetime.now().isoformat()
                })
            
            return results
            
        except Exception as e:
            logger.error(f"LinkedIn search error: {str(e)}")
            return []
    
    def _search_glassdoor(
        self,
        query: str,
        location: str,
        max_results: int
    ) -> List[Dict]:
        """Search Glassdoor via RapidAPI"""
        if not self.rapidapi_key:
            return []
        
        try:
            url = "https://glassdoor-job-search.p.rapidapi.com/search"
            
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "glassdoor-job-search.p.rapidapi.com"
            }
            
            params = {
                "query": query,
                "location": location,
                "page": "1"
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            jobs = data.get('jobs', [])[:max_results]
            
            results = []
            for job in jobs:
                results.append({
                    'id': job.get('jobId', ''),
                    'title': job.get('jobTitle', ''),
                    'company': job.get('employer', ''),
                    'location': job.get('location', ''),
                    'description': job.get('jobDescription', ''),
                    'salary': self._parse_salary(job.get('salary', '')),
                    'salary_text': job.get('salary', 'Not specified'),
                    'rating': job.get('rating'),
                    'url': job.get('jobUrl', ''),
                    'source': 'glassdoor',
                    'timestamp': datetime.now().isoformat()
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Glassdoor search error: {str(e)}")
            return []
    
    def _deduplicate_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Remove duplicate job listings"""
        if not jobs:
            return []
        
        unique_jobs = []
        seen_jobs = set()
        
        for job in jobs:
            # Create unique key from title and company
            title = job.get('title', '').lower().strip()
            company = job.get('company', '').lower().strip()
            job_key = f"{title}:{company}"
            
            if job_key not in seen_jobs:
                unique_jobs.append(job)
                seen_jobs.add(job_key)
        
        return unique_jobs
    
    def _sort_jobs(self, jobs: List[Dict], min_salary: Optional[int]) -> List[Dict]:
        """Sort jobs by relevance and salary"""
        if not jobs:
            return []
        
        # Sort by salary (descending) if salary data available
        def sort_key(job):
            salary = job.get('salary', 0) or 0
            # Prioritize jobs with salary info
            has_salary = 1 if salary > 0 else 0
            return (has_salary, salary)
        
        return sorted(jobs, key=sort_key, reverse=True)
    
    @staticmethod
    def _parse_salary(salary_text: str) -> Optional[int]:
        """Parse salary from text to numeric value"""
        if not salary_text or salary_text == 'Not specified':
            return None
        
        try:
            # Remove common text
            salary_text = salary_text.lower()
            salary_text = salary_text.replace('$', '').replace(',', '')
            salary_text = salary_text.replace('k', '000').replace('per year', '')
            salary_text = salary_text.replace('per hour', '').replace('a year', '')
            
            # Extract numbers
            import re
            numbers = re.findall(r'\d+', salary_text)
            if numbers:
                # Return average if range
                if len(numbers) >= 2:
                    return (int(numbers[0]) + int(numbers[1])) // 2
                return int(numbers[0])
            return None
        except:
            return None
    
    def _get_mock_job_results(
        self,
        query: str,
        location: str,
        max_results: int,
        remote_only: bool,
        min_salary: Optional[int]
    ) -> Dict[str, Any]:
        """Return mock job results for demo/testing"""
        mock_jobs = [
            {
                'id': 'mock-job-1',
                'title': f'{query} Developer',
                'company': 'Tech Company A',
                'location': location or 'San Francisco, CA',
                'description': f'We are looking for a {query} developer to join our growing team.',
                'salary': 120000,
                'salary_text': '$100k - $140k',
                'job_type': 'Full-time',
                'remote': not remote_only,
                'posted_date': '2025-11-20',
                'url': 'https://example.com/job1',
                'source': 'demo',
                'timestamp': datetime.now().isoformat(),
                'tags': ['remote', 'senior'],
                'requirements': ['3+ years experience', 'Strong coding skills'],
                'benefits': ['Health insurance', 'Remote work', 'Competitive salary']
            },
            {
                'id': 'mock-job-2',
                'title': f'{query} Engineer',
                'company': 'Tech Company B',
                'location': 'Remote',
                'description': f'Join us as a {query} engineer and make an impact.',
                'salary': 130000,
                'salary_text': '$110k - $150k',
                'job_type': 'Full-time',
                'remote': True,
                'posted_date': '2025-11-19',
                'url': 'https://example.com/job2',
                'source': 'demo',
                'timestamp': datetime.now().isoformat(),
                'tags': ['remote', 'mid-level'],
                'requirements': ['5+ years experience'],
                'benefits': ['Stock options', 'Health insurance']
            },
            {
                'id': 'mock-job-3',
                'title': f'{query} Specialist',
                'company': 'Tech Company C',
                'location': location or 'New York, NY',
                'description': f'Seeking a {query} specialist for our NYC office.',
                'salary': 95000,
                'salary_text': '$85k - $105k',
                'job_type': 'Full-time',
                'remote': False,
                'posted_date': '2025-11-18',
                'url': 'https://example.com/job3',
                'source': 'demo',
                'timestamp': datetime.now().isoformat(),
                'tags': ['entry-level'],
                'requirements': ['1+ years experience', 'Degree required'],
                'benefits': ['Health insurance', '401k']
            }
        ]
        
        # Apply filters
        filtered = mock_jobs
        if remote_only:
            filtered = [j for j in filtered if j.get('remote')]
        if min_salary:
            filtered = [j for j in filtered if (j.get('salary') or 0) >= min_salary]
        
        filtered = filtered[:max_results]
        
        return {
            'query': query,
            'location': location,
            'jobs': filtered,
            'results': filtered,
            'sources': {'demo': filtered},
            'metadata': {
                'total_results': len(filtered),
                'sources_searched': ['demo'],
                'timestamp': datetime.now().isoformat(),
                'note': 'Mock data - configure RAPIDAPI_KEY for real results'
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get job search statistics"""
        return {
            **self.stats,
            'success_rate': (
                self.stats['successful_searches'] / self.stats['total_searches'] * 100
                if self.stats['total_searches'] > 0 else 0
            ),
            'avg_jobs_per_search': (
                self.stats['total_jobs_returned'] / self.stats['total_searches']
                if self.stats['total_searches'] > 0 else 0
            )
        }


class JobAlertManager:
    """
    Manages job alerts similar to price alerts.
    """
    
    def __init__(self, storage_path: str = './data/job_alerts.json'):
        """Initialize job alert manager"""
        import json
        
        self.storage_path = storage_path
        self.alerts = {}
        
        # Email configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        
        self._load_alerts()
        logger.info(f"Job Alert Manager initialized with {len(self.alerts)} alerts")
    
    def create_alert(
        self,
        user_email: str,
        keywords: str,
        location: str,
        remote_only: bool = False,
        min_salary: Optional[int] = None
    ) -> str:
        """Create a new job alert"""
        import uuid
        alert_id = str(uuid.uuid4())
        
        self.alerts[alert_id] = {
            'id': alert_id,
            'user_email': user_email,
            'keywords': keywords,
            'location': location,
            'remote_only': remote_only,
            'min_salary': min_salary,
            'created_at': datetime.now().isoformat(),
            'is_active': True,
            'last_checked': None,
            'jobs_found': 0
        }
        
        self._save_alerts()
        logger.info(f"Created job alert: {alert_id}")
        return alert_id
    
    def _load_alerts(self):
        """Load alerts from storage"""
        import json
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    self.alerts = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load job alerts: {str(e)}")
    
    def _save_alerts(self):
        """Save alerts to storage"""
        import json
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump(self.alerts, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save job alerts: {str(e)}")
    
    def get_user_alerts(self, user_email: str) -> List[Dict]:
        """Get all alerts for a user"""
        return [
            alert for alert in self.alerts.values()
            if alert['user_email'] == user_email and alert['is_active']
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        total_alerts = len(self.alerts)
        active_alerts = sum(1 for a in self.alerts.values() if a['is_active'])
        
        return {
            'total_alerts': total_alerts,
            'active_alerts': active_alerts
        }