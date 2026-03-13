from apscheduler.schedulers.background import BackgroundScheduler

from app.cert_checker import check_certificate
from app.models import get_all_domains, save_check_result

scheduler = BackgroundScheduler()


def check_domain(domain_id: int, domain: str):
    result = check_certificate(domain)
    save_check_result(domain_id, result)
    return result


def check_all_domains():
    domains = get_all_domains()
    for domain in domains:
        check_domain(domain["id"], domain["domain"])


def start_scheduler():
    if scheduler.get_job("cert_check") is None:
        scheduler.add_job(
            id="cert_check",
            func=check_all_domains,
            trigger="cron",
            hour=2,
            minute=0,
        )

    if not scheduler.running:
        scheduler.start()


def get_next_run_time():
    job = scheduler.get_job("cert_check")
    return job.next_run_time if job else None
