# Aurora Dark

A dark variant of the default **Aurora** theme for FlaskBB.

## Usage

Only `src/scss/_variables.scss`, a dark `_pygments.scss`,
and a few hard-coded light colors in the partials differ from Aurora.

Aurora Dark has no `node_modules` of its own. Its webpack config resolves all
dependencies from `../aurora/node_modules`, so build the Aurora theme first
(`cd ../aurora && npm install`), then from this directory run:

```bash
npm run build     # production build -> static/app.css
npm run watch     # rebuild on change
```
