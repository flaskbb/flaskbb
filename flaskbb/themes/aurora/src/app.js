import { Alert, Tooltip, Dropdown, Modal } from 'bootstrap';

import "./app/emoji.js";
import "./app/editor.js";
import "./app/flaskbb.js";
import "./app/confirm_modal.js";


import "./scss/styles.scss";
export { BulkActions, show_management_search, check_overview_status } from "./app/flaskbb.js";
export { EDITORS } from './app/editor.js';

var tooltips = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"], [data-tooltip="tooltip"]'))
var tooltipList = tooltips.map(function (el) {
  return new Tooltip(el)
})

// import all assets in ./assets
function importAll(r) {
  return r.keys().map(r);
}
importAll(require.context('./assets', false, /\.(png|jpe?g|svg|ico)$/));
