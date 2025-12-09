"""
Job Search Client
Aggregates job postings from multiple sources
"""

import os
import logging
import requests
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class JobSearchClient:
    """
    Unified client for searching job postings.
    Supports Indeed, LinkedIn, Glassdoor via RapidAPI
    """
    
    # --- CONFIGURATION (Integrated API Sources) ---
    # Define API sources using their unique RapidAPI host and base path for flexible switching.
    API_SOURCES = {
        'indeed': {
            # NOTE: Updated to a conceptual working endpoint structure for Indeed
            'host': 'indeed-job-search-v2.p.rapidapi.com',
            'url': 'https://indeed-job-search-v2.p.rapidapi.com/jobs/search',
            'param_map': {'q': 'query', 'l': 'location', 'limit': 'max_results'} # Example mapping
        },
        'linkedin': {
            # LinkedIn API Host based on your provided URL
            'host': 'linkedin-job-search-api.p.rapidapi.com',
            'url': 'https://linkedin-job-search-api.p.rapidapi.com/search',
            'param_map': {'keywords': 'query', 'locationId': 'location', 'results_per_page': 'max_results'}
        },
        'glassdoor': {
            # Glassdoor API endpoint details
            'host': 'glassdoor-job-search.p.rapidapi.com',
            'url': 'https://glassdoor-job-search.p.rapidapi.com/search'
        }
    }
    # ---------------------------------------------
    
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
        
        if not self.rapidapi_key:
            logger.warning("JobSearchClient initialized without RAPIDAPI_KEY. Searches will fail.")
            
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
        Search for jobs across multiple platforms using the API_SOURCES configuration.
        """
        self.stats['total_searches'] += 1
        
        if not self.rapidapi_key:
            logger.warning("RapidAPI key not configured. Using mock job data.")
            return self._get_mock_job_results(query, location, max_results, remote_only, min_salary)
        
        if not sources:
            sources = ['indeed', 'linkedin', 'glassdoor']

        # Normalize job_type and experience_level
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
        with ThreadPoolExecutor(max_workers=len(sources)) as executor:
            futures = {}
            
            for source_name in sources:
                if source_name in self.API_SOURCES:
                     futures[source_name] = executor.submit(
                        self._search_single_source, 
                        source_name, 
                        query, 
                        location, 
                        max_results,
                        remote_only, 
                        min_salary, 
                        experience_level, 
                        job_type
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

    def _search_single_source(
        self,
        source_name: str,
        query: str,
        location: str,
        max_results: int,
        remote_only: bool,
        min_salary: Optional[int],
        experience_level: Optional[str],
        job_type: Optional[str]
    ) -> List[Dict]:
        """
        Generic search function for one source, handling API specific details.
        """
        source_config = self.API_SOURCES.get(source_name)
        if not source_config:
            raise ValueError(f"Source configuration not found for: {source_name}")
            
        url = source_config['url']
        host = source_config['host']
        
        headers = {
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": host
        }
        
        # Base parameters for all jobs APIs
        params = {
            "query": query,
            "location": location,
            "limit": max_results,
            # Common filters to pass through
            "remote": remote_only,
            "salary": min_salary,
            "experience": experience_level,
            "job_type": job_type
        }
        
        # --- Source-Specific Parameter Adjustments ---
        if source_name == 'indeed':
            # Example adjustment based on a conceptual Indeed API on RapidAPI
            params['q'] = params.pop('query')
            params['l'] = params.pop('location')
            params['jt'] = params.pop('job_type') # Indeed often uses 'jt' for job type
            params['remotejob'] = 'true' if params.pop('remote') else 'false'
            # Filter internal params not recognized by the external API
            for key in ['salary', 'experience']: 
                if key in params: del params[key]

        elif source_name == 'linkedin':
            # Parameters often vary significantly; requires specific mapping
            params['keywords'] = params.pop('query')
            params['workplaceType'] = 'remote' if params.pop('remote') else 'hybrid/onsite'
            params['experienceLevel'] = params.pop('experience')
            
            # Filter internal params
            for key in ['location', 'salary', 'job_type']: 
                if key in params: del params[key]
        
        elif source_name == 'glassdoor':
            # Similar specific parameter mapping would be done here
            pass

        # Remove None values and convert booleans to strings for API call
        params = {k: v for k, v in params.items() if v is not None}
        for k, v in params.items():
            if isinstance(v, bool):
                params[k] = str(v).lower()
        
        # Execute the API call
        response = requests.get(url, headers=headers, params=params, timeout=20)
        response.raise_for_status()
        
        data = response.json()
        
        # The key step: Normalize the results from the raw API response
        return self._normalize_job_results(data, source_name)


    def _search_indeed(
        self,
        query: str,
        location: str,
        max_results: int,
        remote_only: bool,
        min_salary: Optional[int],
        job_type: Optional[str]
    ) -> List[Dict]:
        """Deprecated: Use _search_single_source."""
        # This method is now obsolete and redirects the call to the generic handler
        return self._search_single_source(
            'indeed', query, location, max_results, remote_only, min_salary, None, job_type
        )
    
    def _search_linkedin(
        self,
        query: str,
        location: str,
        max_results: int,
        remote_only: bool,
        experience_level: Optional[str]
    ) -> List[Dict]:
        """Deprecated: Use _search_single_source."""
        # This method is now obsolete and redirects the call to the generic handler
        return self._search_single_source(
            'linkedin', query, location, max_results, remote_only, min_salary=None, experience_level=experience_level, job_type=None
        )
    
    def _search_glassdoor(
        self,
        query: str,
        location: str,
        max_results: int
    ) -> List[Dict]:
        """Deprecated: Use _search_single_source."""
        # This method is now obsolete and redirects the call to the generic handler
        return self._search_single_source(
            'glassdoor', query, location, max_results, remote_only=False, min_salary=None, experience_level=None, job_type=None
        )
    
    def _normalize_job_results(self, data: Dict, source_name: str) -> List[Dict]:
        """
        Transforms raw API data into a standardized job format. 
        This part requires careful mapping specific to each API's JSON structure.
        """
        normalized = []
        
        # --- MAPPING Logic ---
        if source_name == 'linkedin':
            # Assuming the LinkedIn API returns a list under the 'data' key
            items = data.get('data', [])
            for item in items:
                # NOTE: The mapping below assumes job details are top-level or easy to access
                salary = self._parse_salary(item.get('salaryRange', ''))
                
                normalized.append({
                    'id': item.get('jobId'),
                    'title': item.get('title'),
                    'company': item.get('companyName'),
                    'location': item.get('location'),
                    'description': item.get('description'),
                    'salary': salary,
                    'salary_text': item.get('salaryRange', 'Not specified'),
                    'job_type': item.get('jobType'),
                    'remote': item.get('workplaceType', '').lower() == 'remote',
                    'posted_date': item.get('postedDate'),
                    'url': item.get('applyUrl'),
                    'source': 'linkedin',
                    'timestamp': datetime.now().isoformat()
                })
        
        elif source_name == 'indeed':
            # Assuming the Indeed API returns a list under the 'hits' key (common in API v2)
            items = data.get('hits', [])
            for item in items:
                salary = self._parse_salary(item.get('salary', ''))
                
                normalized.append({
                    'id': item.get('jobkey'),
                    'title': item.get('title'),
                    'company': item.get('companyName'),
                    'location': item.get('location'),
                    'description': item.get('summary'),
                    'salary': salary,
                    'salary_text': item.get('salary', 'Not specified'),
                    'job_type': item.get('jobType'),
                    'remote': 'remote' in item.get('type', '').lower(),
                    'posted_date': item.get('date'),
                    'url': item.get('url'),
                    'source': 'indeed',
                    'timestamp': datetime.now().isoformat()
                })
        
        elif source_name == 'glassdoor':
            # Assuming the Glassdoor API returns results under the 'jobs' key
            items = data.get('jobs', [])
            for item in items:
                salary = self._parse_salary(item.get('salary', ''))
                
                normalized.append({
                    'id': item.get('jobId'),
                    'title': item.get('jobTitle'),
                    'company': item.get('employer'),
                    'location': item.get('location'),
                    'description': item.get('jobDescription'),
                    'salary': salary,
                    'salary_text': item.get('salary', 'Not specified'),
                    'job_type': item.get('jobType'),
                    'remote': 'remote' in item.get('jobTitle', '').lower(),
                    'posted_date': item.get('date'),
                    'url': item.get('jobUrl'),
                    'source': 'glassdoor',
                    'timestamp': datetime.now().isoformat()
                })
        # --- END MAPPING Logic ---
        
        return normalized

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
            # Simple normalization to catch variations
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
            
            numbers = re.findall(r'\d+', salary_text)
            if numbers:
                # Return average if range
                if len(numbers) >= 2:
                    # Use integer division for clean dollar amounts
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