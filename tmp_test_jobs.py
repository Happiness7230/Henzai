import os
from src.jobs.job_search_client import JobSearchClient

# Print environment RAPIDAPI_KEY status
print('RAPIDAPI_KEY in env:', 'RAPIDAPI_KEY' in os.environ)

client = JobSearchClient()

try:
    res = client.search_jobs('python', location='Remote', max_results=5, remote_only=True)
    print('Returned metadata keys:', res.get('metadata', {}).keys())
    print('Total results:', res.get('metadata', {}).get('total_results'))
    print('Number of jobs:', len(res.get('jobs', [])))
    print('Sample:', res.get('jobs', [None])[0])
except Exception as e:
    print('Exception when calling search_jobs:', type(e), e)
    import traceback
    traceback.print_exc()
