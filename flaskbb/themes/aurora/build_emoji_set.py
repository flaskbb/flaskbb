import string
from contextlib import suppress

import requests


with open('src/js/emoji.js', 'w') as f:
    source = requests.get(
        'https://raw.githubusercontent.com/github/gemoji/master/db/emoji.json'
    ).json()
    output = set()

    for item in source:
        with suppress(KeyError):
            for alias in item['aliases'] + [item['description']]:
                output.add((
                    ''.join(filter(
                        set(
                            string.ascii_letters
                            + string.digits
                            + '+-'
                        ).__contains__,
                        (
                            alias
                            .lower()
                            .replace(' ', '-')
                            .replace('_', '-')
                            .replace('&', 'and')
                        )
                    )),
                    item['emoji']
                ))

    f.write('var emojies = [\n')
    for name, character in sorted(output,
                                  key=lambda t: (len(t[0]), t[0])):
        f.write('    ["{}", "{}"],\n'.format(name, character))
    f.write('];')
