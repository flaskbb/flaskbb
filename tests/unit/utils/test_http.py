# taken from Django 3.2.0.alpha0 and adapted to run in pytest
from flaskbb.utils.http import is_safe_url


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
        assert not is_safe_url(bad_url, allowed_hosts={"testserver", "testserver2"})


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
        assert is_safe_url(good_url, allowed_hosts={"otherserver", "testserver"})


def test_basic_auth():
    # Valid basic auth credentials are allowed.
    assert is_safe_url(
        r"http://user:pass@testserver/", allowed_hosts={"user:pass@testserver"}
    )


def test_no_allowed_hosts():
    # A path without host is allowed.
    assert is_safe_url("/confirm/me@example.com", allowed_hosts=None)
    # Basic auth without host is not allowed.
    assert not is_safe_url(r"http://testserver\@example.com", allowed_hosts=None)


def test_allowed_hosts_str():
    assert is_safe_url("http://good.com/good", allowed_hosts="good.com")
    assert not is_safe_url("http://good.co/evil", allowed_hosts="good.com")


def test_secure_param_https_urls():
    secure_urls = (
        "https://example.com/p",
        "HTTPS://example.com/p",
        "/view/?param=http://example.com",
    )
    for url in secure_urls:
        assert is_safe_url(url, allowed_hosts={"example.com"}, require_https=True)


def test_secure_param_non_https_urls():
    insecure_urls = (
        "http://example.com/p",
        "ftp://example.com/p",
        "//example.com/p",
    )
    for url in insecure_urls:
        assert not is_safe_url(url, allowed_hosts={"example.com"}, require_https=True)
