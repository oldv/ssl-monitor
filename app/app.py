import os

from flask import Flask, jsonify, render_template, request

from app.cert_checker import check_certificate
from app.models import (
    add_domain,
    delete_domain,
    get_dingtalk_config,
    get_domains_with_latest_check,
    init_db,
    upsert_dingtalk_config,
)
from app.scheduler import check_domain, check_all_domains, get_next_run_time, start_scheduler

app = Flask(__name__, template_folder="templates", static_folder="static")


def _should_start_scheduler():
    # Avoid double-start in Flask reloader
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        return True
    return not app.debug


@app.route("/")
def index():
    domains = get_domains_with_latest_check()
    next_run = get_next_run_time()
    return render_template("index.html", domains=domains, next_run=next_run)


@app.route("/dingtalk")
def dingtalk_settings():
    config = get_dingtalk_config()
    return render_template("dingtalk.html", config=config)


@app.route("/api/domains", methods=["POST"])
def api_add_domain():
    data = request.get_json(force=True, silent=True) or {}
    domain = data.get("domain", "")
    try:
        domain_id = add_domain(domain)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    return jsonify({"success": True, "id": domain_id})


@app.route("/api/domains/<int:domain_id>", methods=["DELETE"])
def api_delete_domain(domain_id: int):
    delete_domain(domain_id)
    return jsonify({"success": True})


@app.route("/api/check/<int:domain_id>", methods=["POST"])
def api_check_domain(domain_id: int):
    data = request.get_json(force=True, silent=True) or {}
    domain = data.get("domain")
    if not domain:
        # fall back to DB if not provided
        domains = get_domains_with_latest_check()
        match = next((d for d in domains if d["id"] == domain_id), None)
        if not match:
            return jsonify({"success": False, "error": "domain not found"}), 404
        domain = match["domain"]

    result = check_domain(domain_id, domain)
    return jsonify({"success": True, "result": result})


@app.route("/api/check-all", methods=["POST"])
def api_check_all():
    check_all_domains()
    return jsonify({"success": True})


@app.route("/api/dingtalk/test", methods=["POST"])
def api_test_dingtalk():
    data = request.get_json(force=True, silent=True) or {}
    msg = (data.get("msg") or "SSL Monitor 测试消息").strip()
    config = get_dingtalk_config()
    if not config:
        return jsonify({"success": False, "error": "请先保存 access_token 与 secret"}), 400

    try:
        from app.send_custom_robot_group_message import send_custom_robot_group_message

        send_custom_robot_group_message(config["access_token"], config["secret"], msg)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

    return jsonify({"success": True})


@app.route("/api/dingtalk", methods=["POST"])
def api_save_dingtalk():
    data = request.get_json(force=True, silent=True) or {}
    access_token = (data.get("access_token") or "").strip()
    secret = (data.get("secret") or "").strip()
    if not access_token or not secret:
        return jsonify({"success": False, "error": "access_token 与 secret 均不能为空"}), 400

    upsert_dingtalk_config(access_token, secret)
    return jsonify({"success": True})


@app.route("/api/check-now", methods=["POST"])
def api_check_now():
    data = request.get_json(force=True, silent=True) or {}
    domain = data.get("domain", "")
    if not domain:
        return jsonify({"success": False, "error": "domain required"}), 400
    result = check_certificate(domain)
    return jsonify({"success": True, "result": result})


def _bootstrap():
    init_db()
    if _should_start_scheduler():
        start_scheduler()


_bootstrap()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
