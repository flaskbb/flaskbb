import { isHidden } from "./utils";

function replyEditor() {
    return document.querySelector(".flaskbb-editor");
}

function showEditor(editor) {
    if (!isHidden(editor)) return;
    // the preview button toggles the editor back from its preview
    document.querySelector(`.preview-btn[data-preview="${editor.id}"]`)?.click();
}

function leadingNewlines(before) {
    if (before === "" || before.endsWith("\n\n")) return "";
    return before.endsWith("\n") ? "\n" : "\n\n";
}

export function insertQuote(editor, quote) {
    showEditor(editor);

    // the caret of an editor that was never focused sits at the start, where a
    // quote would push the reply that is already written below it
    if (editor.selectionStart === 0 && editor.selectionEnd === 0) {
        editor.selectionStart = editor.selectionEnd = editor.value.length;
    }
    const text = leadingNewlines(editor.value.slice(0, editor.selectionStart)) + quote;

    editor.focus({ preventScroll: true });
    // execCommand keeps the insertion on the textarea's undo stack
    if (!document.execCommand("insertText", false, text)) {
        editor.setRangeText(text, editor.selectionStart, editor.selectionEnd, "end");
        editor.dispatchEvent(new Event("input", { bubbles: true }));
    }

    editor.scrollIntoView({ behavior: "smooth", block: "center" });
    editor.classList.add("quote-inserted");
    editor.addEventListener("animationend", () => editor.classList.remove("quote-inserted"), {
        once: true,
    });
}

// mirrors flaskbb.utils.helpers.format_quote
function formatQuote(post, linkText, text) {
    const { quoteAuthor, quoteAuthorUrl, quotePostUrl } = post.dataset;
    const body = text
        .replace(/\r\n?/g, "\n")
        .replace(/\n{3,}/g, "\n\n")
        .split("\n")
        .join("\n> ");
    return (
        `> **[${quoteAuthor}](${quoteAuthorUrl}) wrote:** [${linkText}](${quotePostUrl})\n` +
        `>\n> ${body}\n\n`
    );
}

function quotableSelection() {
    const selection = document.getSelection();
    if (!selection || selection.isCollapsed || selection.rangeCount === 0) return null;

    const text = selection.toString().trim();
    if (!text) return null;

    const range = selection.getRangeAt(0);
    let node = range.commonAncestorContainer;
    if (node.nodeType !== Node.ELEMENT_NODE) node = node.parentElement;
    const post = node.closest(".post-content[data-quote-post-url]");
    if (!post) return null;

    return { post, text, range };
}

function placeSelectionButton() {
    const button = document.querySelector(".selection-quote-btn");
    if (!button) return;

    const selected = replyEditor() && quotableSelection();
    if (!selected) {
        button.hidden = true;
        return;
    }

    button.hidden = false;
    const rect = selected.range.getBoundingClientRect();
    const halfWidth = button.offsetWidth / 2 + 8;
    const center = rect.left + rect.width / 2;
    const below = rect.top < button.offsetHeight + 16;

    button.classList.toggle("below", below);
    button.style.top = `${below ? rect.bottom : rect.top}px`;
    button.style.left = `${Math.min(Math.max(center, halfWidth), window.innerWidth - halfWidth)}px`;
}

let placementPending = false;
function schedulePlacement() {
    if (placementPending) return;
    placementPending = true;
    requestAnimationFrame(() => {
        placementPending = false;
        placeSelectionButton();
    });
}

document.addEventListener("selectionchange", schedulePlacement);
window.addEventListener("scroll", schedulePlacement, { passive: true });
window.addEventListener("resize", schedulePlacement);

// keep the selection alive while the button is pressed
document.addEventListener("mousedown", (event) => {
    if (event.target.closest(".selection-quote-btn")) event.preventDefault();
});

document.addEventListener("click", (event) => {
    const button = event.target.closest(".selection-quote-btn");
    if (!button) return;

    const editor = replyEditor();
    const selected = quotableSelection();
    if (!editor || !selected) return;

    insertQuote(editor, formatQuote(selected.post, button.dataset.linkText, selected.text));
    document.getSelection().removeAllRanges();
    button.hidden = true;
});

// quote a whole post. delegated, so it keeps working on posts htmx swapped in
document.addEventListener("click", (event) => {
    const button = event.target.closest(".quote-btn");
    if (!button) return;

    // without a reply editor on the page the link opens the full reply form
    const editor = replyEditor();
    if (!editor) return;
    event.preventDefault();

    const urlprefix = typeof FORUM_URL_PREFIX !== "undefined" ? FORUM_URL_PREFIX : "";
    fetch(`${urlprefix}/post/${button.dataset.postId}/raw`)
        .then((response) => {
            // an expired session redirects to the login page, which the full
            // reply form handles properly
            if (response.redirected) {
                window.location.href = button.href;
                return null;
            }
            if (!response.ok) throw new Error(response.statusText);
            return response.text();
        })
        .then((quote) => {
            if (quote !== null) insertQuote(editor, quote);
        })
        .catch((error) => {
            console.error("could not load the quoted post", error);
        });
});
