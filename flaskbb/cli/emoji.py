import re
import shutil
import tarfile
from pathlib import Path, PurePosixPath
from tempfile import TemporaryFile

import click
import requests
from flask import current_app
from flask.cli import with_appcontext

from flaskbb.cli.main import flaskbb

TWEMOJI_VERSION = "17.0.3"


@flaskbb.command("download-emoji", short_help="Download Twemoji SVGs into static/emoji/.")
@with_appcontext
def download_emoji():
    destination = Path(current_app.static_folder) / "emoji"
    url = f"https://codeload.github.com/jdecked/twemoji/tar.gz/refs/tags/v{TWEMOJI_VERSION}"
    click.echo(f"Downloading Twemoji {TWEMOJI_VERSION}...")
    count = 0
    try:
        with TemporaryFile() as download:
            with requests.get(url, stream=True, timeout=60) as response:
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=65536):
                    download.write(chunk)
            download.seek(0)
            with tarfile.open(fileobj=download, mode="r:gz") as archive:
                destination.mkdir(parents=True, exist_ok=True)
                for member in archive:
                    path = PurePosixPath(member.name)
                    if not member.isfile():
                        continue
                    is_svg = path.parts[1:-1] == ("assets", "svg") and re.fullmatch(
                        r"[0-9a-f]+(?:-[0-9a-f]+)*\.svg", path.name
                    )
                    is_license = len(path.parts) == 2 and path.name == "LICENSE-GRAPHICS"
                    if not is_svg and not is_license:
                        continue
                    with archive.extractfile(member) as source:
                        with (destination / path.name).open("wb") as target:
                            shutil.copyfileobj(source, target)
                    if is_svg:
                        count += 1
    except (requests.RequestException, tarfile.TarError, OSError) as error:
        raise click.ClickException(f"Could not download emoji: {error}") from error
    if not count:
        raise click.ClickException("The Twemoji archive contained no SVGs.")
    click.echo(f"Downloaded {count} emoji SVGs to {destination}.")
    click.echo("Set EMOJI_BASE_URL = None in your config to serve these files locally.")
