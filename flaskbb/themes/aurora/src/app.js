import "marked/lib/marked";
import "jquery-textcomplete/dist/jquery.textcomplete.min"
import "bootstrap-sass/assets/javascripts/bootstrap.min"
import "bootstrap-markdown/js/bootstrap-markdown"

import "./js/emoji"
import "./js/editor"
import "./js/flaskbb"


import "./scss/styles.scss"


// import all assets in ./assets
function importAll(r) {
  return r.keys().map(r);
}
importAll(require.context('./assets', false, /\.(png|jpe?g|svg|ico)$/));
