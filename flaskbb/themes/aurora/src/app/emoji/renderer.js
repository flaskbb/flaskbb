import emojiRegex from "emoji-regex";

const excludedSelector = "code, pre, textarea, select, script, style, noscript, iframe, svg, [contenteditable]";
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
        acceptNode: (node) => node.parentElement.closest(excludedSelector)
            ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT,
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
            const assetCharacter = character.includes("\u200D") ? character : character.replace(/\uFE0F/g, "");
            const codepoint = Array.from(assetCharacter, (character) => character.codePointAt(0).toString(16)).join("-");
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
