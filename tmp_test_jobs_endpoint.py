from src.web.app import app, initialize_components
import json

# Initialize components (so job_search_client is created)
initialize_components()

client = app.test_client()

payload = {
    'q': 'python',
    'location': 'Remote',
    'job_type': ['Full-time'],
    'experience_level': 'mid',
    'remote_only': True,
    'min_salary': None,
    'max_results': 30
}

resp = client.post('/api/jobs/search', data=json.dumps(payload), content_type='application/json')
print('Status code:', resp.status_code)
try:
    print('JSON:', resp.get_json())
except Exception as e:
    print('Failed to parse JSON:', e)
    print('Response data:', resp.data)
