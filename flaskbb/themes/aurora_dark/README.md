# Aurora Dark

A dark variant of the default **Aurora** theme for FlaskBB.

## Usage

`src/scss/` only contains three files: `_variables.scss` (the color
palette), `_pygments.scss` (a dark Pygments stylesheet), and `styles.scss`.
Everything else is imported directly from `../aurora/src/scss/` by relative path
in `styles.scss`, so there is a single shared copy of each partial. Colors that
differ between the two themes overridden here in this theme's `_variables.scss`.

Aurora Dark has no `node_modules` of its own. Its webpack config resolves all
dependencies from `../aurora/node_modules`, so build the Aurora theme first
(`cd ../aurora && npm install`), then from this directory run:

```bash
npm run build     # production build -> static/app.css
npm run watch     # rebuild on change
```
