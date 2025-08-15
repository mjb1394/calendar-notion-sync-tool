from apscheduler.schedulers.background import BackgroundScheduler
from notion_calendar_sync.web import services

scheduler = BackgroundScheduler()

def start_sync_job(interval_minutes: int):
    """
    Starts the scheduled sync job.
    If a job is already running, it will be rescheduled with the new interval.
    """
    job_id = 'notion_sync'
    if scheduler.get_job(job_id):
        scheduler.reschedule_job(job_id, trigger='interval', minutes=interval_minutes)
    else:
        scheduler.add_job(
            services.run_sync,
            'interval',
            minutes=interval_minutes,
            id=job_id
        )
    if not scheduler.running:
        scheduler.start()

def stop_sync_job():
    """
    Stops the scheduled sync job.
    """
    job_id = 'notion_sync'
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    if not scheduler.get_jobs() and scheduler.running:
        scheduler.shutdown()

def get_job_status():
    """
    Gets the status of the sync job.
    """
    job_id = 'notion_sync'
    job = scheduler.get_job(job_id)
    if job:
        return {
            "status": "running",
            "next_run": job.next_run_time.isoformat()
        }
    return {"status": "stopped"}
