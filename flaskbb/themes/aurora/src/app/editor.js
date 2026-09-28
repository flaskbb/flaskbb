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

function setEditorMode(toolbar, editor, preview, mode) {
    const writeButton = toolbar.querySelector(".write-btn");
    const previewButton = toolbar.querySelector(".preview-btn");

    if (mode === "write") {
        activateButtons(toolbar);
        showElement(editor);
        hideElement(preview);
    } else {
        disableButtons(toolbar);
        hideElement(editor);
        showElement(preview);
    }

    if (!writeButton) return;
    const isWriting = mode === "write";
    writeButton.classList.toggle("btn-primary", isWriting);
    writeButton.classList.toggle("btn-white", !isWriting);
    writeButton.classList.toggle("active", isWriting);
    writeButton.setAttribute("aria-pressed", isWriting.toString());
    previewButton.classList.toggle("btn-primary", !isWriting);
    previewButton.classList.toggle("btn-white", isWriting);
    previewButton.classList.toggle("active", !isWriting);
    previewButton.setAttribute("aria-pressed", (!isWriting).toString());
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

    if (!isHidden(previewContainer) && toolbar.querySelector(".write-btn")) {
        return;
    }

    if (!isHidden(previewContainer)) {
        setEditorMode(toolbar, markdownContainer, previewContainer, "write");
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

        setEditorMode(toolbar, markdownContainer, previewContainer, "preview");
    });
}

// the server enforces the same minimum and only returns usernames that
// markup.MENTION_REGEX would turn into a profile link
const USER_LOOKUP_MIN_LENGTH = 3;
const USERNAME_CHARS = "[\\p{L}\\p{N}_\\-]";

function notInCode(text) {
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
}

function lookupUsers({ excludeSelf = false } = {}) {
    let timer = null;
    let controller = null;
    return (term, callback) => {
        clearTimeout(timer);
        controller?.abort();
        timer = setTimeout(() => {
            controller = new AbortController();
            const params = new URLSearchParams({ q: term });
            if (excludeSelf) {
                params.set("exclude_self", "1");
            }
            fetch(`${document.body.dataset.userLookupUrl}?${params}`, {
                signal: controller.signal,
                headers: { Accept: "application/json" },
            })
                .then((response) => (response.ok ? response.json() : []))
                .then(callback)
                .catch((error) => {
                    if (error.name !== "AbortError") {
                        callback([]);
                    }
                });
        }, 200);
    };
}

function renderUser(user) {
    const item = document.createElement("span");
    const avatar = document.createElement("img");
    avatar.src = user.avatar_url;
    avatar.alt = "";
    avatar.width = 20;
    avatar.height = 20;
    avatar.className = "rounded-circle me-2";
    item.append(avatar, user.username);
    return item.innerHTML;
}

function mentionStrategy() {
    return {
        id: "mention",
        match: new RegExp(`\\B@(${USERNAME_CHARS}{${USER_LOOKUP_MIN_LENGTH},})$`, "u"),
        search: lookupUsers(),
        cache: true,
        replace: (user) => `@${user.username} `,
        template: renderUser,
        context: notInCode,
    };
}

const AUTOCOMPLETE_CONFIG = {
    dropdown: {
        maxCount: 5,
    },
};

function autocomplete(element) {
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
        context: notInCode,
    };
    const strategies = [emojiStrategy];
    if (document.body.dataset.userLookupUrl) {
        strategies.push(mentionStrategy());
    }
    return new Textcomplete(new TextareaEditor(element), strategies, AUTOCOMPLETE_CONFIG);
}

function userLookupInput(element) {
    const strategy = {
        id: "user-lookup",
        match: new RegExp(`^(${USERNAME_CHARS}{${USER_LOOKUP_MIN_LENGTH},})$`, "u"),
        search: lookupUsers({ excludeSelf: true }),
        cache: true,
        replace: (user) => user.username,
        template: renderUser,
    };
    return new Textcomplete(new TextareaEditor(element), [strategy], AUTOCOMPLETE_CONFIG);
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

document.addEventListener("click", (event) => {
    const button = event.target.closest(".write-btn");
    if (!button) return;
    event.preventDefault();

    const editor = document.querySelector(`#${button.dataset.editor}`);
    const preview = document.querySelector(`#${button.dataset.editor}-preview`);
    const toolbar = button.closest("markdown-toolbar");
    setEditorMode(toolbar, editor, preview, "write");
    editor.focus();
});

htmx.onLoad((root) => {
    root.querySelectorAll(".flaskbb-editor").forEach((el) => autocomplete(el));
    if (document.body.dataset.userLookupUrl) {
        root.querySelectorAll("input[data-user-lookup]").forEach((el) => userLookupInput(el));
    }
    root.querySelectorAll("[data-autoresize=true]").forEach((el) => autoresize(el));
});
