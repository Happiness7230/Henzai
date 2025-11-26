from src.web.app import app, initialize_components, api_job_search
import json

initialize_components()

payload = {
    'q': 'python',
    'location': 'Remote',
    'job_type': ['Full-time'],
    'experience_level': 'mid',
    'remote_only': True,
    'min_salary': None,
    'max_results': 30
}

with app.test_request_context('/api/jobs/search', method='POST', json=payload):
    resp = api_job_search()
    # resp can be a tuple or Response; normalize
    try:
        if isinstance(resp, tuple):
            body, status = resp
            print('Status:', status)
            try:
                print('Body JSON:', body.get_json())
            except Exception:
                print('Body:', body)
        else:
            print('Status:', resp.status_code)
            try:
                print('JSON:', resp.get_json())
            except Exception:
                print('Data:', resp.data)
    except Exception as e:
        print('Error handling response:', e)
        import traceback
        traceback.print_exc()
