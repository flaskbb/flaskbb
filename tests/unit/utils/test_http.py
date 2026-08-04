# taken from Django 3.2.0.alpha0 and adapted to run in pytest
from urllib.parse import parse_qs

from flaskbb.utils.http import (
    _normalize_url,
    get_first_safe_redirect_url,
    get_safe_redirect_url,
)

ALLOWED_HOSTS = {"localhost:5000", "example.com"}


def test_get_safe_redirect_url_falls_back_to_default_for_tab_payload():
    # http://localhost:5000/auth/login?next=/%09///google.com
    #
    decoded = parse_qs("next=/%09///google.com")["next"][0]
    assert decoded == "/\t///google.com"
    assert decoded[1] == "\x09"

    # Werkzeug/urllib percent-decode the query string before application code
    # ever sees it, so by the time `next` reaches `is_safe_url` it already
    # contains a real tab byte (0x09), not the literal text "%09".
    result = get_safe_redirect_url("/\t///google.com", ALLOWED_HOSTS, fallback="/dashboard")
    assert result == "/dashboard"


def test_get_first_safe_redirect_url_skips_tab_payload_and_uses_next_candidate():
    result = get_first_safe_redirect_url(
        "/\t///google.com",  # malicious `next`
        "http://evil.com/x",  # malicious referrer
        allowed_hosts=ALLOWED_HOSTS,
        fallback="/dashboard",
    )
    assert result == "/dashboard"


def test_strips_embedded_tab():
    assert _normalize_url("/\t///google.com") == "////google.com"


def test_strips_leading_control_character():
    assert _normalize_url("\t///google.com") == "///google.com"


def test_strips_embedded_carriage_return_and_newline():
    assert _normalize_url("/\r\n///google.com") == "////google.com"


def test_leaves_ordinary_urls_untouched():
    assert _normalize_url("/dashboard") == "/dashboard"
    assert _normalize_url("https://example.com/x") == "https://example.com/x"


def test_does_not_decode_percent_encoded_control_characters():
    assert _normalize_url("/%09///example.com") == "/%09///example.com"


def test_empty_string_after_stripping_returns_empty():
    assert _normalize_url("\t\r\n") == ""


def test_get_safe_redirect_url_passes_through_allowed_url():
    result = get_safe_redirect_url("/profile", ALLOWED_HOSTS, fallback="/dashboard")
    assert result == "/profile"


def test_get_first_safe_redirect_url_prefers_first_valid_candidate():
    result = get_first_safe_redirect_url(
        "/profile",
        "https://example.com/other",
        allowed_hosts=ALLOWED_HOSTS,
        fallback="/dashboard",
    )
    assert result == "/profile"


def test_bad_urls():
    bad_urls = (
        "http://example.com",
        "http:///example.com",
        "https://example.com",
        "ftp://example.com",
        r"\\example.com",
        r"\\\example.com",
        r"/\\/example.com",
        r"\\\example.com",
        r"\\example.com",
        r"\\//example.com",
        r"/\/example.com",
        r"\/example.com",
        r"/\example.com",
        "http:///example.com",
        r"http:/\//example.com",
        r"http:\/example.com",
        r"http:/\example.com",
        'javascript:alert("XSS")',
        "\njavascript:alert(x)",
        "\x08//example.com",
        r"http://otherserver\@example.com",
        r"http:\\testserver\@example.com",
        r"http://testserver\me:pass@example.com",
        r"http://testserver\@example.com",
        r"http:\\testserver\confirm\me@example.com",
        "http:999999999",
        "ftp:9999999999",
        "\n",
        "http://[2001:cdba:0000:0000:0000:0000:3257:9652/",
        "http://2001:cdba:0000:0000:0000:0000:3257:9652]/",
    )
    for bad_url in bad_urls:
        assert not get_safe_redirect_url(bad_url, allowed_hosts={"testserver", "testserver2"})


def test_good_urls():
    good_urls = (
        "/view/?param=http://example.com",
        "/view/?param=https://example.com",
        "/view?param=ftp://example.com",
        "view/?param=//example.com",
        "https://testserver/",
        "HTTPS://testserver/",
        "//testserver/",
        "http://testserver/confirm?email=me@example.com",
        "/url%20with%20spaces/",
        "path/http:2222222222",
    )
    for good_url in good_urls:
        assert get_safe_redirect_url(good_url, allowed_hosts={"otherserver", "testserver"})


def test_basic_auth():
    # Valid basic auth credentials are allowed.
    assert get_safe_redirect_url(
        r"http://user:pass@testserver/", allowed_hosts={"user:pass@testserver"}
    )


def test_no_allowed_hosts():
    # A path without host is allowed.
    assert get_safe_redirect_url("/confirm/me@example.com", allowed_hosts=None)
    # Basic auth without host is not allowed.
    assert not get_safe_redirect_url(r"http://testserver\@example.com", allowed_hosts=None)


def test_allowed_hosts_str():
    assert get_safe_redirect_url("http://good.com/good", allowed_hosts="good.com")
    assert not get_safe_redirect_url("http://good.co/evil", allowed_hosts="good.com")


def test_secure_param_https_urls():
    secure_urls = (
        "https://example.com/p",
        "HTTPS://example.com/p",
        "/view/?param=http://example.com",
    )
    for url in secure_urls:
        assert get_safe_redirect_url(url, allowed_hosts={"example.com"}, require_https=True)


def test_secure_param_non_https_urls():
    insecure_urls = (
        "http://example.com/p",
        "ftp://example.com/p",
        "//example.com/p",
    )
    for url in insecure_urls:
        assert not get_safe_redirect_url(url, allowed_hosts={"example.com"}, require_https=True)
