from collections import namedtuple
from os import path

import pytest

from responses import RequestsMock, Response


@pytest.fixture(scope="function")
def responses():
    mock = RequestsMock(assert_all_requests_are_fired=True)
    with mock:
        yield mock


_here = __file__


ImageResponse = namedtuple("ImageResponse", ["raw", "url", "headers"])


def _get_image_bytes(which):
    img_path = path.join(path.realpath(path.dirname(_here)), "images", which)
    with open(img_path, "rb") as fh:
        return fh.read()


def _get_image_resp(which, mime):
    raw = _get_image_bytes(which)
    return Response(
        method="GET",
        body=raw,
        url="http://example/{}".format(which),
        headers={"Content-Type": mime, "Content-Length": str(len(raw))},
        stream=True,
    )


@pytest.fixture(scope="function")
def image_just_right():
    return _get_image_resp("good_image.png", "image/png")


@pytest.fixture(scope="function")
def image_too_big():
    return _get_image_resp("too_big.gif", "image/gif")


@pytest.fixture(scope="function")
def image_too_tall():
    return _get_image_resp("too_tall.png", "image/png")


@pytest.fixture(scope="function")
def image_too_wide():
    return _get_image_resp("too_wide.png", "image/png")


@pytest.fixture(scope="function")
def image_wrong_mime():
    return _get_image_resp("wrong_mime.svg", "image/svg+xml")


@pytest.fixture(scope="function")
def image_jpg():
    return _get_image_resp("image.jpg", "image/jpeg")


@pytest.fixture(scope="function")
def image_gif():
    return _get_image_resp("image.gif", "image/gif")


@pytest.fixture(scope="function")
def image_png():
    return _get_image_resp("image.png", "image/png")
