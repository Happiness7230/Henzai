from celery import Celery
import logging
from src.jobs.email_notifications import send_job_alert_email, send_price_alert_email

logger = logging.getLogger(__name__)

celery = Celery(
    "search_engine",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

celery.conf.timezone = "UTC"
celery.conf.enable_utc = True

@celery.task
def check_job_alerts():
    """Background task to check job alerts"""
    from src.jobs.job_search_client import JobSearchClient, JobAlertManager
    
    alert_manager = JobAlertManager()
    job_client = JobSearchClient()
    
    alerts = [a for a in alert_manager.alerts.values() if a['is_active']]
    
    for alert in alerts:
        try:
            results = job_client.search_jobs(
                query=alert['keywords'],
                location=alert['location'],
                remote_only=alert['remote_only'],
                min_salary=alert['min_salary'],
                max_results=5
            )
            
            if results['jobs']:
                # Send notification email
                send_job_alert_email(alert, results['jobs'])
                
        except Exception as e:
            logger.error(f"Error checking job alert {alert['id']}: {e}")

# Add to beat schedule
celery.conf.beat_schedule['check-job-alerts-daily'] = {
    'task': 'celery_app.check_job_alerts',
    'schedule': 86400.0,  # Daily
}