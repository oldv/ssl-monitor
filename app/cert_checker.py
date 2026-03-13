import os
import socket
import ssl
import tempfile
from datetime import datetime, timezone


def _split_host_port(domain: str, default_port: int = 443):
    domain = domain.strip()
    if not domain:
        raise ValueError("empty domain")

    # Handle simple host:port (ignore IPv6 brackets for now)
    if ":" in domain and domain.count(":") == 1:
        host, port_str = domain.rsplit(":", 1)
        if port_str.isdigit():
            return host, int(port_str)

    return domain, default_port


def check_certificate(domain: str, timeout: int = 5):
    try:
        host, port = _split_host_port(domain)
        host_idna = host.encode("idna").decode("ascii")

        ctx = ssl.create_default_context()
        # Allow fetching even if the cert is expired or hostname mismatch
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with socket.create_connection((host_idna, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host_idna) as ssock:
                cert_der = ssock.getpeercert(binary_form=True)

        if not cert_der:
            return {
                "status": "error",
                "error_msg": "certificate data missing",
            }

        pem = ssl.DER_cert_to_PEM_cert(cert_der)
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(pem.encode("ascii"))
                tmp_path = tmp.name

            cert = ssl._ssl._test_decode_cert(tmp_path)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

        if not cert or "notAfter" not in cert:
            return {
                "status": "error",
                "error_msg": "certificate data missing",
            }

        expires = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
        expires = expires.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        days_left = (expires - now).days

        issuer = "Unknown"
        issuer_pairs = cert.get("issuer") or []
        try:
            issuer = dict(x[0] for x in issuer_pairs).get("commonName", "Unknown")
        except Exception:
            issuer = "Unknown"

        status = "expired" if days_left < 0 else "valid"

        return {
            "status": status,
            "expires_on": expires.date(),
            "days_left": days_left,
            "issuer": issuer,
        }
    except Exception as exc:
        return {
            "status": "error",
            "error_msg": str(exc),
        }
