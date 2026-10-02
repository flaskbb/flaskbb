import emojiRegex from "emoji-regex";
import keywords from "emojilib" with { type: "json" };
import aliases from "./emoji/aliases.json" with { type: "json" };

const emojis = Object.entries(keywords).map(([character, names]) => ({
    character,
    name: names[0],
    aliases: aliases[character] || [],
    keywords: names,
}));

export const commonEmoji = "😄 😂 😉 😊 😍 😎 🤔 😢 😭 😱 😡 😅 👍 👎 👋 👏 🙏 💪 ❤️ 💔 🎉 🔥 💯 ☕"
    .split(" ")
    .map((character) => emojis.find((emoji) => emoji.character === character));

export function searchEmoji(term, limit = 5) {
    const query = term
        .toLowerCase()
        .replace(/\s+/g, "_")
        .replace(/(\w)-(?=\w)/g, "$1_");
    const matches = [];
    for (const emoji of emojis) {
        if (matches.length >= limit) {
            return matches;
        }
        if (emoji.name === query || emoji.aliases.includes(query)) {
            matches.push(emoji);
        }
    }
    for (const emoji of emojis) {
        if (matches.length >= limit) {
            break;
        }
        if (emoji.name === query || emoji.aliases.includes(query)) {
            continue;
        }
        if (
            emoji.aliases.some((name) => name.includes(query)) ||
            emoji.keywords.some((name) => name.includes(query))
        ) {
            matches.push(emoji);
        }
    }
    return matches;
}

const excludedSelector =
    "code, pre, textarea, select, script, style, noscript, iframe, svg, [contenteditable]";
const assetAliases = {
    "1f441-fe0f-200d-1f5e8-fe0f": "1f441-200d-1f5e8",
    "1f441-fe0f-200d-1f5e8": "1f441-200d-1f5e8",
    "1f441-200d-1f5e8-fe0f": "1f441-200d-1f5e8",
};

function replaceMissingEmoji(event) {
    if (event.target.tagName === "IMG" && event.target.classList.contains("emoji")) {
        event.target.replaceWith(document.createTextNode("[emoji]"));
    }
}

export function renderEmoji(element) {
    if (element.closest(excludedSelector)) {
        return;
    }
    const emojiBase = document.body.dataset.emojiBase.replace(/\/?$/, "/");
    document.addEventListener("error", replaceMissingEmoji, true);
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, {
        acceptNode: (node) =>
            node.parentElement.closest(excludedSelector)
                ? NodeFilter.FILTER_REJECT
                : NodeFilter.FILTER_ACCEPT,
    });
    const nodes = [];
    while (walker.nextNode()) {
        nodes.push(walker.currentNode);
    }
    const regex = emojiRegex();
    for (const node of nodes) {
        const text = node.nodeValue;
        let fragment;
        let offset = 0;
        for (const match of text.matchAll(regex)) {
            const character = match[0];
            const end = match.index + character.length;
            if (["©", "®", "™"].includes(character) || text[end] === "\uFE0E") {
                continue;
            }
            fragment ??= document.createDocumentFragment();
            const assetCharacter = character.includes("\u200D")
                ? character
                : character.replace(/\uFE0F/g, "");
            const codepoint = Array.from(assetCharacter, (character) =>
                character.codePointAt(0).toString(16),
            ).join("-");
            const image = document.createElement("img");
            image.className = "emoji";
            image.alt = character;
            image.draggable = false;
            image.src = `${emojiBase}${assetAliases[codepoint] || codepoint}.svg`;
            if (match.index > offset) {
                fragment.append(text.slice(offset, match.index));
            }
            fragment.append(image);
            offset = end;
        }
        if (offset) {
            if (offset < text.length) {
                fragment.append(text.slice(offset));
            }
            node.replaceWith(fragment);
        }
    }
}

export function emojiContext(text) {
    let fence = null;
    let inlineTicks = 0;
    const lines = text.split("\n");

    for (const line of lines) {
        const content = line.replace(/^(?: {0,3}> ?)+/, "");
        const marker = content.match(/^ {0,3}(`{3,}|~{3,})(.*)$/);
        if (fence) {
            if (
                marker &&
                marker[1][0] === fence.character &&
                marker[1].length >= fence.length &&
                !marker[2].trim()
            ) {
                fence = null;
            }
            continue;
        }
        if (marker && !inlineTicks && (marker[1][0] !== "`" || !marker[2].includes("`"))) {
            fence = { character: marker[1][0], length: marker[1].length };
            continue;
        }
        for (let index = 0; index < content.length; index++) {
            if (content[index] === "\\" && !inlineTicks) {
                index++;
                continue;
            }
            if (content[index] !== "`") {
                continue;
            }
            let count = 1;
            while (content[index + count] === "`") {
                count++;
            }
            if (!inlineTicks) {
                inlineTicks = count;
            } else if (count === inlineTicks) {
                inlineTicks = 0;
            }
            index += count - 1;
        }
    }
    return !fence && !inlineTicks && !/^(?: {4}|\t)/.test(lines.at(-1));
}

export function emojiStrategy() {
    return {
        id: "emoji",
        match: /(^|[\s([{]):([a-z0-9_+-]*):?$/i,
        index: 2,
        context: emojiContext,
        search: (term, callback) => {
            callback(searchEmoji(term));
        },
        replace: (emoji) => `$1${emoji.character} `,
        template: (emoji) => {
            const item = document.createElement("span");
            const character = document.createElement("span");
            character.setAttribute("aria-hidden", "true");
            character.textContent = emoji.character;
            renderEmoji(character);
            item.append(character, ` ${emoji.name}`);
            return item.innerHTML;
        },
    };
}

function showResults(picker) {
    const query = picker.querySelector("input").value.trim();
    const emojis = query ? searchEmoji(query, 48) : commonEmoji;
    const results = picker.querySelector(".emoji-picker-results");
    results.replaceChildren(
        ...emojis.map((emoji) => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "btn btn-white";
            button.dataset.emoji = emoji.character;
            button.title = emoji.name.replaceAll("_", " ");
            button.setAttribute("aria-label", button.title);
            button.textContent = emoji.character;
            return button;
        }),
    );
    picker.querySelector(".emoji-picker-empty").hidden = emojis.length > 0;
    renderEmoji(results);
}

export function initializeEmoji({ htmx, Modal }) {
    let editor;
    let selectionStart;
    let selectionEnd;

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
        if (event.target.id === "emoji-search") {
            showResults(event.target.closest(".modal"));
        }
    });

    document.addEventListener("shown.bs.modal", (event) => {
        if (event.target.id === "emoji-picker") {
            event.target.querySelector("input").focus();
        }
    });

    document.addEventListener("hidden.bs.modal", (event) => {
        if (event.target.id !== "emoji-picker") {
            return;
        }
        if (editor?.isConnected) {
            editor.focus();
        }
        editor = null;
    });

    document.addEventListener("htmx:beforeCleanupElement", (event) => {
        if (editor && event.detail.elt.contains(editor)) {
            editor = null;
            Modal.getInstance(document.getElementById("emoji-picker")).hide();
        }
    });

    htmx.onLoad(renderEmoji);
}
