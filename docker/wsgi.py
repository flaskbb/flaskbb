"""WSGI entry point for the container images.

The configuration is picked up from the FLASKBB_SETTINGS environment
variable, see docker/flaskbb.cfg.
"""

import os

from flaskbb.app import create_app

flaskbb = create_app()

if os.environ.get("PROXY_FIX", "").strip().lower() in {"1", "true", "yes", "on"}:
    from werkzeug.middleware.proxy_fix import ProxyFix

    _hops = int(os.environ.get("PROXY_FIX_HOPS", "1"))
    flaskbb.wsgi_app = ProxyFix(
        flaskbb.wsgi_app, x_for=_hops, x_proto=_hops, x_host=_hops, x_prefix=_hops
    )
