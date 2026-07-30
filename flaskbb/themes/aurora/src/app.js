import '@flaskbb/markdown-toolbar-element';
import { Alert, Dropdown, Modal, Tooltip } from 'bootstrap';

import "./app/confirm_modal.js";
import "./app/editor.js";
import "./app/emoji.js";
import "./app/flaskbb.js";


import "./scss/styles.scss";
export { Actions, BulkActions, check_overview_status, show_management_search } from "./app/flaskbb.js";

var flaskbbAllowList = Tooltip.Default.allowList
// allow <time> elements
flaskbbAllowList.time = []

var tooltips = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"], [data-tooltip="tooltip"]'))
var tooltipList = tooltips.map(function (el) {
  return new Tooltip(el)
})

// import all assets in ./assets
function importAll(r) {
  return r.keys().map(r);
}
importAll(require.context('./assets', false, /\.(png|jpe?g|svg|ico)$/));
