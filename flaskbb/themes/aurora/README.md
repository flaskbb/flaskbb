# FlaskBB's Default Theme

Make sure that you have npm (nodejs) installed. You can get it from
[here](https://nodejs.org).

Before you can compile the source, you need to get a few dependencies first.
This can be achieved by running ``npm install`` in the directory where
**this** README is located.

# Usage

To minimize the dependencies to build and minify our source files, we just use
npm for it.

    Usage
      npm run [TASK]

    Available tasks
      clean
        rm -f node_modules
      build
        npx webpack --config webpack.prod.js
      watch
        npx webpack --config webpack.dev.js --watch


To watch for changes in our JS and SCSS files, you just have to run:
```bash
npm run watch
```
and upon changes it will automatically rebuild the files.

To build a production bundle, you have to run webpack with the prod config:
```bash
npm run build
```

# Create your own theme

See the [theming](https://flaskbb.readthedocs.io/en/latest/theming.html)
documentation.

# Emoji

Emoji remain Unicode in stored posts. Rendered pages, previews, autocomplete
suggestions, and the picker use the same Twemoji 17.0.3 SVG artwork. Code and editable
fields remain plain text. Failed images display `[emoji]` instead of switching to
the user's system emoji font.

Use the smile button to choose a common emoji or search the catalog. It inserts
Unicode at the cursor, replacing any selected text. You can also type `:smile`
and select a completion with Enter or Tab. Search uses the
[emojilib](https://github.com/muan/emojilib) keyword catalog and the short aliases
in `src/app/emoji/aliases.json`. The catalog is bundled with the theme; no catalog
generation, browser preferences, or separate data downloads are needed.

Artwork is served from jsDelivr by default. To host it yourself:

1. Download the [Twemoji 17.0.3 source archive](https://github.com/jdecked/twemoji/archive/refs/tags/v17.0.3.tar.gz).
2. Copy the contents of `assets/svg/` into your installation's
   `flaskbb/static/emoji/` directory, and retain `LICENSE-GRAPHICS` with the assets.
3. Set `EMOJI_BASE_URL = None` in `instance/flaskbb.cfg` and restart FlaskBB.

FlaskBB generates the local static URL, including any deployment URL prefix.
Alternatively, set `EMOJI_BASE_URL = "/emoji/twemoji-17.0.3/"` to use a directory
served by your web server, or provide an absolute URL for another asset host.
The URL must point directly to the SVG files. No frontend rebuild is needed when
changing this setting, and local hosting does not fall back to a CDN.

Twemoji graphics are copyright Twitter, Inc. and other contributors, licensed
under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Emojilib is MIT licensed.
