import { TextareaEditor } from "@textcomplete/textarea";
import { Textcomplete } from "@textcomplete/core";
import htmx from "htmx.org";
import EMOJIS from "./emoji";
import { hideElement, isHidden, showElement } from "./utils";
import { parse_emoji } from "./flaskbb";

const buttonSelectors = [
    "md-header",
    "md-bold",
    "md-italic",
    "md-quote",
    "md-code",
    "md-link",
    "md-image",
    "md-unordered-list",
    "md-ordered-list",
    "md-task-list",
    "md-mention",
    "md-strikethrough",
    ".help-btn",
];
function disableButtons(toolbar) {
    for (const button of toolbar.querySelectorAll(buttonSelectors.join(", "))) {
        button.classList.add("disabled");
    }
}

function activateButtons(toolbar) {
    for (const button of toolbar.querySelectorAll(buttonSelectors.join(", "))) {
        button.classList.remove("disabled");
    }
}

function markdownPreview(element) {
    const editorId = element.dataset.preview
    const toolbar = document.querySelector(`markdown-toolbar[for="${editorId}"]`)
    const markdownContainer = document.querySelector(
        `#${editorId}`
    );
    const previewContainer = document.querySelector(
        `#${editorId}-preview`
    );

    if (!isHidden(previewContainer)) {
        activateButtons(toolbar);
        showElement(markdownContainer);
        hideElement(previewContainer);
        return;
    }

    // rendered by the server with the same renderer and markdown plugins as the
    // saved post. no source element, so the request inherits hx-* attributes
    // from <body> only and not from the page the editor sits in
    htmx.ajax("POST", element.dataset.previewUrl, {
        target: previewContainer,
        swap: "innerHTML",
        values: { text: markdownContainer.value },
    }).then(() => {
        previewContainer.style.minHeight = `${markdownContainer.scrollHeight}px`;
        previewContainer.style.height = "auto";

        disableButtons(toolbar);
        hideElement(markdownContainer);
        showElement(previewContainer);
    });
}

function autocomplete(element) {
    const config = {
        dropdown: {
            maxCount: 5,
        },
    };

    const emojiStrategy = {
        id: "emoji",
        match: /\B:([\-+\w]*)$/,
        search: (term, callback) => {
            callback(
                EMOJIS.map((value) => {
                    return value[0].indexOf(term) !== -1
                        ? { character: value[1], name: value[0] }
                        : null;
                })
            );
        },
        replace: (value) => {
            return `${value.character} `;
        },
        template: (value) => {
            return parse_emoji(value.character) + " " + value.name;
        },
        context: (text) => {
            const blockmatch = text.match(/`{3}/g);
            if (blockmatch && blockmatch.length % 2) {
                // Cursor is in a code block
                return false;
            }
            const inlinematch = text.match(/`/g);
            if (inlinematch && inlinematch.length % 2) {
                // Cursor is in a inline code
                return false;
            }
            return true;
        },
    };
    return new Textcomplete(new TextareaEditor(element), [emojiStrategy], config);
}

function autoresize(element) {
    element.setAttribute(
        "style",
        "height:" + element.scrollHeight + "px;overflow-y:hidden;"
    );
    element.addEventListener(
        "input",
        function (e) {
            e.target.style.height = "auto";
            e.target.style.height = e.target.scrollHeight + "px";
        },
        false
    );
}

// delegated, so it also works for editors htmx swapped in
document.addEventListener("click", (event) => {
    const button = event.target.closest(".preview-btn");
    if (!button) return;
    event.preventDefault();
    markdownPreview(button);
});

htmx.onLoad((root) => {
    root.querySelectorAll(".flaskbb-editor").forEach((el) => autocomplete(el));
    root.querySelectorAll("[data-autoresize=true]").forEach((el) => autoresize(el));
});
