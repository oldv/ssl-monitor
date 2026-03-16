import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from app.cert_checker import check_certificate
from app.models import DEFAULT_ALERT_DAYS, get_all_domains, get_dingtalk_config, save_check_result
from app.send_custom_robot_group_message import send_custom_robot_group_message

scheduler = BackgroundScheduler()


def _format_alert_message(domain: str, result: dict):
    expires_on = result.get("expires_on")
    days_left = result.get("days_left")
    issuer = result.get("issuer") or "Unknown"
    status = result.get("status") or "unknown"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    if days_left is None:
        days_text = "未知"
    elif days_left < 0:
        days_text = f"已过期 {-days_left} 天"
    else:
        days_text = f"{days_left} 天"

    return (
        "SSL 证书告警\n"
        f"域名：{domain}\n"
        f"状态：{status}\n"
        f"剩余：{days_text}\n"
        f"到期：{expires_on}\n"
        f"颁发者：{issuer}\n"
        f"时间：{now}"
    )


def _maybe_send_alert(domain: str, result: dict):
    if result.get("status") not in {"valid", "expired"}:
        return

    config = get_dingtalk_config()
    if not config:
        return

    try:
        alert_days = int(config.get("alert_days", DEFAULT_ALERT_DAYS))
    except (TypeError, ValueError):
        alert_days = DEFAULT_ALERT_DAYS

    days_left = result.get("days_left")
    if days_left is None or days_left > alert_days:
        return

    msg = _format_alert_message(domain, result)
    try:
        send_custom_robot_group_message(config["access_token"], config["secret"], msg)
    except Exception as exc:
        logging.exception("Failed to send DingTalk alert: %s", exc)


def check_domain(domain_id: int, domain: str):
    result = check_certificate(domain)
    save_check_result(domain_id, result)
    _maybe_send_alert(domain, result)
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
