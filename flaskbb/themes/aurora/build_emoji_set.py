import sys
import re

import requests


URL = 'https://unicode.org/Public/emoji/{}/emoji-test.txt'.format(sys.argv[1])


def get_annotations():
    resp = requests.get(URL)
    resp.raise_for_status()
    for line in resp.text.split('\n'):
        match = re.match('(.+?); fully-qualified +?# .+? (.+)', line)
        if match is not None:
            yield (
                ''.join(chr(int(h, 16))
                        for h in
                        match.group(1).strip().split(' ')),
                match.group(2)
            )


with open('src/js/emoji.js', 'w') as f:
    f.write('var emojies = [\n')
    for character, name in get_annotations():
        name = name.replace(':', '').replace(' ', '_')
        f.write('    ["{}", "{}"],\n'.format(name, character))
    f.write('];\n')
