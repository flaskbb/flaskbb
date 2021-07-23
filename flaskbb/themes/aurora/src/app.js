import "bootstrap-sass/assets/javascripts/bootstrap.min";

import "./app/emoji.js";
import "./app/editor.js";
import "./app/flaskbb.js";
//import "./app/confirm_modal.js";


import "./scss/styles.scss";
export { BulkActions, show_management_search } from "./app/flaskbb.js";

// import all assets in ./assets
function importAll(r) {
  return r.keys().map(r);
}
importAll(require.context('./assets', false, /\.(png|jpe?g|svg|ico)$/));
