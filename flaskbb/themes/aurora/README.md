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
