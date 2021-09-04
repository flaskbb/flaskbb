import { TextareaEditor } from "@textcomplete/textarea";
import { Textcomplete } from "@textcomplete/core";
import EMOJIS from "./emoji";
import { parse_emoji } from "./flaskbb";

const TEXTCOMPLETE_CONFIG = {
    dropdown: {
        maxCount: 5
    }
}

const EMOJI_STRATEGY = {
    id: "emoji",
    match: /\B:([\-+\w]*)$/,
    search: (term, callback) => {
        callback(EMOJIS.map(value => {
            return value[0].indexOf(term) !== -1 ? { character: value[1], name: value[0] } : null;
        }))
    },
    replace: (value) => {
        return `${value.character} `;
    },
    template: (value) => {
        return parse_emoji(value.character) + ' ' + value.name;
    },
    context: (text) => {
        const blockmatch = text.match(/`{3}/g)
        if (blockmatch && blockmatch.length % 2) {
            // Cursor is in a code block
            return false
        }
        const inlinematch = text.match(/`/g)
        if (inlinematch && inlinematch.length % 2) {
            // Cursor is in a inline code
            return false
        }
        return true
    },
}

function configureAutocomplete(element) {
    const editor = new TextareaEditor(element)
    const textcomplete = new Textcomplete(editor, [EMOJI_STRATEGY], TEXTCOMPLETE_CONFIG)
}


function setupEditor() {
    const editors = document.querySelectorAll(".flaskbb-editor");
    for(const e of editors) {
        configureAutocomplete(e);
    }
}


function markdownPreview(element) {

}


function autoresizeTextarea(element) {
    element.setAttribute(
        "style",
        "height:" + element.scrollHeight + "px;overflow-y:hidden;"
    );
    element.addEventListener(
        "input",
        function (e) {
            console.log(e)
            e.target.style.height = "auto";
            e.target.style.height = e.target.scrollHeight + "px";
        },
        false
    );
}

const tareas = document.querySelectorAll("[data-autoresize=true]");
for (const e of tareas) {
    autoresizeTextarea(e);
}

setupEditor()
