import re
import sys

import requests

URL = f"https://unicode.org/Public/emoji/{sys.argv[1]}/emoji-test.txt"


def get_annotations():
    resp = requests.get(URL, timeout=(3.05, 27))
    resp.raise_for_status()
    for line in resp.text.split("\n"):
        match = re.match("(.+?); fully-qualified +?# .+? (.+)", line)
        if match is not None:
            yield (
                "".join(chr(int(h, 16)) for h in match.group(1).strip().split(" ")),
                match.group(2),
            )


def format_name(name):
    # name is somthing like: E11_big_smile
    # --> convert it to big_smile
    return "_".join(name.split("_")[1:])


with open("src/app/emoji.js", "w") as f:
    f.write("const EMOJIS = [\n")
    for character, name in get_annotations():
        name = name.replace(":", "").replace(" ", "_")
        f.write(f'    ["{format_name(name)}", "{character}"],\n')
    f.write("];\n")
