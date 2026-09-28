"""Health check of the web containers: fetches a static file through the app.

An open port alone proves nothing, gunicorn binds it before its workers have
loaded the app. The request has to carry a Host header the app accepts,
otherwise TRUSTED_HOSTS rejects it with a 400.

Usage: healthcheck.py <port>
"""

import os
import sys
import urllib.request

trusted_hosts = [host.strip() for host in os.environ.get("TRUSTED_HOSTS", "").split(",")]
host = os.environ.get("SERVER_NAME") or trusted_hosts[0].lstrip(".") or "localhost"

request = urllib.request.Request(
    f"http://127.0.0.1:{sys.argv[1]}/static/favicon.ico", headers={"Host": host}
)
with urllib.request.urlopen(request, timeout=5):
    pass
