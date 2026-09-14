import '@flaskbb/markdown-toolbar-element';
import { Alert, Dropdown, Modal, Tooltip } from 'bootstrap';
import htmx from 'htmx.org';

import "./app/confirm_modal.js";
import "./app/editor.js";
import "./app/emoji.js";
import "./app/flaskbb.js";


import "./scss/styles.scss";
export { Actions, check_overview_status, show_management_search } from "./app/flaskbb.js";

// htmx has to be reachable via window. plugins register extensions against it and
// templates outside this bundle call into it.
window.htmx = htmx;

var flaskbbAllowList = Tooltip.Default.allowList
// allow <time> elements
flaskbbAllowList.time = []

htmx.onLoad(function (root) {
  root.querySelectorAll('[data-bs-toggle="tooltip"], [data-tooltip="tooltip"]').forEach(function (el) {
    Tooltip.getOrCreateInstance(el)
  })
})

// a tooltip still open on an element htmx removes would stay on screen
document.addEventListener('htmx:beforeCleanupElement', function (event) {
  var tooltip = Tooltip.getInstance(event.target)
  if (tooltip) tooltip.dispose()
})

document.addEventListener('click', function (event) {
  var toggle = event.target.closest('.tree-toggle')
  if (!toggle) return
  event.preventDefault()
  var parent = toggle.closest('.tree-parent')
  var expanded = parent.classList.toggle('expanded')
  toggle.setAttribute('aria-expanded', expanded ? 'true' : 'false')
})

// import all assets in ./assets
function importAll(r) {
  return r.keys().map(r);
}
importAll(require.context('./assets', false, /\.(png|jpe?g|svg|ico)$/));
