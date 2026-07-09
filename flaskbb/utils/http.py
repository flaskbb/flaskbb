# -*- coding: utf-8 -*-
"""
flaskbb.utils.http
~~~~~~~~~~~~~~~~~~

Provides a utility function that attempts to validate an URL against
a set of valid hosts.

See https://www.owasp.org/index.php/Unvalidated_Redirects_and_Forwards_Cheat_Sheet
for more information about this topic.

Note: Most of this code has been taken from Django 3.2.0.alpha0.
"""

import unicodedata
from urllib.parse import urlparse

# Mirrors the WHATWG URL spec's "C0 control or space" trim (applied at both
# ends of the string) and its removal of ASCII tab/newline from anywhere in
# the string. Browsers apply this same normalization when resolving a URL,
# and so does Python's own urllib.parse.urlsplit() internally
_C0_CONTROL_OR_SPACE = "".join(chr(i) for i in range(0x21))  # \x00-\x20 inclusive
_ASCII_TAB_OR_NEWLINE = ("\t", "\r", "\n")


def _normalize_url(url: str) -> str:
    """
    Strip the control characters that browsers and URL parsers silently
    remove/ignore when resolving a URL, so that every check performed on
    ``url`` afterwards sees the same string a browser would ultimately act
    on. This must run before ANY validation logic. Validating a
    not yet normalized string and then using a normalized one (or vice
    versa) is exactly what makes a bypass like `/\t///google.com` possible.
    """
    url = url.strip(_C0_CONTROL_OR_SPACE)
    for c in _ASCII_TAB_OR_NEWLINE:
        url = url.replace(c, "")
    return url


def _url_has_allowed_host_and_scheme(
    url: str, allowed_hosts: set[str], require_https: bool = False
):
    # Sanitize the url:
    # - the "///" prefix check
    # - the control-character check
    url = _normalize_url(url)
    if not url:
        return False

    # Chrome considers any URL with more than two slashes to be absolute, but
    # urlparse is not so flexible. Treat any url with three slashes as unsafe.
    if url.startswith("///"):
        return False
    try:
        url_info = urlparse(url)
    except ValueError:  # e.g. invalid IPv6 addresses
        return False
    # Forbid URLs like http:///example.com - with a scheme, but without a hostname.
    # In that URL, example.com is not the hostname but, a path component. However,
    # Chrome will still consider example.com to be the hostname, so we must not
    # allow this syntax.
    if not url_info.netloc and url_info.scheme:
        return False
    # Forbid URLs that start with control characters. Some browsers (like
    # Chrome) ignore quite a few control characters at the start of a
    # URL and might consider the URL as scheme relative.
    if unicodedata.category(url[0])[0] == "C":
        return False
    scheme = url_info.scheme
    # Consider URLs without a scheme (e.g. //example.com/p) to be http.
    if not url_info.scheme and url_info.netloc:
        scheme = "http"
    valid_schemes = ["https"] if require_https else ["http", "https"]
    return (not url_info.netloc or url_info.netloc in allowed_hosts) and (
        not scheme or scheme in valid_schemes
    )


def get_safe_redirect_url(
    url: str | None,
    allowed_hosts: set[str] | list[str] | str | None,
    fallback: str | None = None,
    require_https: bool = False,
) -> str | None:
    """
    Validate ``url`` and return the URL that should actually be redirected
    to.

    Returns ``fallback`` if ``url`` is missing or fails validation. ``fallback``
    is trusted and is NOT re-validated. Callers must pass something known
    to be safe (e.g. ``url_for("some.view")``), never user input.
    """
    if url is not None:
        url = url.strip()
    if not url:
        return fallback

    normalized = _normalize_url(url)
    normalized_backslashes = _normalize_url(url.replace("\\", "/"))

    if allowed_hosts is None:
        allowed_hosts = set()
    elif isinstance(allowed_hosts, str):
        allowed_hosts = {allowed_hosts}
    elif isinstance(allowed_hosts, list):
        allowed_hosts = set(allowed_hosts)

    if _url_has_allowed_host_and_scheme(
        normalized, allowed_hosts, require_https=require_https
    ) and _url_has_allowed_host_and_scheme(
        normalized_backslashes, allowed_hosts, require_https=require_https
    ):
        return normalized

    return fallback


def get_first_safe_redirect_url(
    *candidates: str | None,
    allowed_hosts: set[str] | list[str] | str | None,
    fallback: str,
    require_https: bool = False,
) -> str:
    """
    Return the first candidate in ``candidates`` (checked in order) that is
    safe to redirect to, normalized. Falsy candidates are skipped.

    Returns ``fallback`` if ``url`` is missing or fails validation. ``fallback``
    is trusted and is NOT re-validated. Callers must pass something known
    to be safe (e.g. ``url_for("some.view")``), never user input.
    """
    for candidate in candidates:
        if not candidate:
            continue
        result = get_safe_redirect_url(
            candidate, allowed_hosts, fallback=None, require_https=require_https
        )
        if result is not None:
            return result
    return fallback
