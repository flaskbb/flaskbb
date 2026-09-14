from pathlib import Path
from typing import Any

from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CompileTranslationsHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        translations = Path(self.root, "flaskbb", "translations")
        for po_path in translations.glob("*/LC_MESSAGES/messages.po"):
            with po_path.open("rb") as po_file:
                catalog = read_po(po_file, locale=po_path.parent.parent.name)
            with po_path.with_suffix(".mo").open("wb") as mo_file:
                write_mo(mo_file, catalog)
