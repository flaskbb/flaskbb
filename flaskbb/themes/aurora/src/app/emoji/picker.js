import { Modal } from "bootstrap";
import { commonEmoji, searchEmoji } from "./catalog.js";
import { renderEmoji } from "./renderer.js";

let editor;
let selectionStart;
let selectionEnd;

function showResults(picker) {
    const query = picker.querySelector("input").value.trim();
    const emojis = query ? searchEmoji(query, 48) : commonEmoji;
    const results = picker.querySelector(".emoji-picker-results");
    results.replaceChildren(...emojis.map((emoji) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "btn btn-white";
        button.dataset.emoji = emoji.character;
        button.title = emoji.name.replaceAll("_", " ");
        button.setAttribute("aria-label", button.title);
        button.textContent = emoji.character;
        return button;
    }));
    picker.querySelector(".emoji-picker-empty").hidden = emojis.length > 0;
    renderEmoji(results);
}

document.addEventListener("click", (event) => {
    const opener = event.target.closest(".emoji-picker-btn");
    if (opener && !opener.classList.contains("disabled")) {
        editor = document.getElementById(opener.dataset.editor);
        selectionStart = editor.selectionStart;
        selectionEnd = editor.selectionEnd;
        const picker = document.getElementById("emoji-picker");
        picker.querySelector("input").value = "";
        showResults(picker);
        Modal.getOrCreateInstance(picker).show();
    }

    const choice = event.target.closest("#emoji-picker button[data-emoji]");
    if (choice && editor?.isConnected) {
        const textarea = editor;
        Modal.getInstance(document.getElementById("emoji-picker")).hide();
        textarea.setSelectionRange(selectionStart, selectionEnd);
        // Keep insertion on the textarea's undo stack where supported.
        if (!document.execCommand("insertText", false, choice.dataset.emoji)) {
            textarea.setRangeText(choice.dataset.emoji, selectionStart, selectionEnd, "end");
            textarea.dispatchEvent(new Event("input", { bubbles: true }));
        }
    }
});

document.addEventListener("input", (event) => {
    if (event.target.id === "emoji-search") showResults(event.target.closest(".modal"));
});

document.addEventListener("shown.bs.modal", (event) => {
    if (event.target.id === "emoji-picker") event.target.querySelector("input").focus();
});

document.addEventListener("hidden.bs.modal", (event) => {
    if (event.target.id !== "emoji-picker") return;
    if (editor?.isConnected) editor.focus();
    editor = null;
});

document.addEventListener("htmx:beforeCleanupElement", (event) => {
    if (editor && event.detail.elt.contains(editor)) {
        editor = null;
        Modal.getInstance(document.getElementById("emoji-picker")).hide();
    }
});
