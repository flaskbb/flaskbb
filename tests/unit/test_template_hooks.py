import re
from pathlib import Path

import flaskbb
from flaskbb.plugins import spec

TEMPLATE_ROOT = Path(flaskbb.__file__).parent
RUN_HOOK_CALL = re.compile(r"run_hook\(")
RUN_HOOK_NAME = re.compile(r"""run_hook\(\s*["']([A-Za-z0-9_]+)["']""")


def template_sources():
    return {path: path.read_text() for path in TEMPLATE_ROOT.rglob("*.html")}


def spec_names():
    return {name for name in dir(spec) if hasattr(getattr(spec, name), "flaskbb_spec")}


def test_run_hook_calls_use_literal_names():
    for path, source in template_sources().items():
        assert len(RUN_HOOK_CALL.findall(source)) == len(RUN_HOOK_NAME.findall(source)), path


def test_run_hook_names_have_specs():
    specs = spec_names()
    unknown = {
        (str(path.relative_to(TEMPLATE_ROOT)), name)
        for path, source in template_sources().items()
        for name in RUN_HOOK_NAME.findall(source)
        if name not in specs
    }

    assert specs
    assert not unknown
