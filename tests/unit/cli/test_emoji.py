import io
import sys
import tarfile
from unittest.mock import MagicMock

import pytest
import requests
from flask import Flask
from flaskbb.cli.emoji import download_emoji


@pytest.fixture
def runner(tmp_path):
    app = Flask(__name__, static_folder=str(tmp_path / "static"))
    with app.app_context():
        yield app.test_cli_runner()


def test_downloads_only_svg_assets_and_license(runner, tmp_path, monkeypatch):
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w:gz") as archive:
        for name, content in [
            ("twemoji-17.0.3/assets/svg/1f604.svg", b"<svg/>"),
            ("twemoji-17.0.3/LICENSE-GRAPHICS", b"graphics license"),
            ("twemoji-17.0.3/assets/72x72/1f604.png", b"png"),
            ("twemoji-17.0.3/assets/svg/../../escaped.svg", b"unsafe"),
        ]:
            member = tarfile.TarInfo(name)
            member.size = len(content)
            archive.addfile(member, io.BytesIO(content))
    response = MagicMock()
    response.__enter__.return_value = response
    response.iter_content.return_value = [data.getvalue()]
    get = MagicMock(return_value=response)
    monkeypatch.setattr(sys.modules["flaskbb.cli.emoji"].requests, "get", get)

    result = runner.invoke(download_emoji)

    assert result.exit_code == 0, result.output
    destination = tmp_path / "static" / "emoji"
    assert {path.name for path in destination.iterdir()} == {"1f604.svg", "LICENSE-GRAPHICS"}
    assert (destination / "1f604.svg").read_bytes() == b"<svg/>"
    assert (destination / "LICENSE-GRAPHICS").read_bytes() == b"graphics license"
    assert "Downloaded 1 emoji SVGs" in result.output
    assert "EMOJI_BASE_URL = None" in result.output
    get.assert_called_once_with(
        "https://codeload.github.com/jdecked/twemoji/tar.gz/refs/tags/v17.0.3",
        stream=True,
        timeout=60,
    )


def test_download_failure(runner, monkeypatch):
    get = MagicMock(side_effect=requests.ConnectionError("connection failed"))
    monkeypatch.setattr(sys.modules["flaskbb.cli.emoji"].requests, "get", get)

    result = runner.invoke(download_emoji)

    assert result.exit_code == 1
    assert "Could not download emoji: connection failed" in result.output


def test_invalid_archive(runner, monkeypatch):
    response = MagicMock()
    response.__enter__.return_value = response
    response.iter_content.return_value = [b"not an archive"]
    monkeypatch.setattr(
        sys.modules["flaskbb.cli.emoji"].requests, "get", MagicMock(return_value=response)
    )

    result = runner.invoke(download_emoji)

    assert result.exit_code == 1
    assert "Could not download emoji" in result.output
