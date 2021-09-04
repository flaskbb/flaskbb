import EasyMDE from "easymde";
import { CodeMirrorEditor } from "@textcomplete/codemirror";
import EMOJIS from "./emoji";
import { Textcomplete } from "@textcomplete/core";
import { parse_emoji } from "./flaskbb";
export const EDITORS = new Map();



function startsWith(term, limit = 10) {
    const results = [];
    // Whether previous key started with the term
    let prevMatch = false
    for (const [key, url] of EMOJIS) {
        if (key.startsWith(term)) {
            results.push([key, url])
            if (results.length === limit) break
            prevMatch = true
        } else if (prevMatch) {
            break
        }
    }
    return results
}


const EMOJI_STRATEGY = {
    id: "emoji",
    match: /\B:([\-+\w]*)$/,
    search: (term, callback) => {
        callback(EMOJIS.map(value => {
            let x =  value[0].indexOf(term) !== -1 ? { character: value[1], name: value[0] } : null;
            return x;
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



function loadEditor(element) {
    const easyMDE = new EasyMDE({
        autoDownloadFontAwesome: false,
        element: element,
        autoRefresh: true,
        forceSync: true,
        spellChecker: false,
        sideBySideFullscreen: false,
        status: false,
    });
    const textCompleteEditor = new CodeMirrorEditor(easyMDE.codemirror);
    const textcomp = new Textcomplete(textCompleteEditor, [EMOJI_STRATEGY], { dropdown: { maxCount: 5 }})
    return easyMDE;
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

const editorsSelector = document.querySelectorAll(".flaskbb-editor");
editorsSelector.forEach((value, index) => {
    if (typeof value.id != 'undefined') {
        EDITORS.set(value.id, loadEditor(value));
    } else {
        EDITORS.set(`easyMDE-${index}`, loadEditor(value));
    }

});
