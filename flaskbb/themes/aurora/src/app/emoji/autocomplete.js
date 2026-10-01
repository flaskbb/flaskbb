import { searchEmoji } from "./catalog.js";
import { renderEmoji } from "./renderer.js";

export function emojiContext(text) {
    let fence = null;
    let inlineTicks = 0;
    const lines = text.split("\n");

    for (const line of lines) {
        const content = line.replace(/^(?: {0,3}> ?)+/, "");
        const marker = content.match(/^ {0,3}(`{3,}|~{3,})(.*)$/);
        if (fence) {
            if (marker && marker[1][0] === fence.character && marker[1].length >= fence.length && !marker[2].trim()) {
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
            if (content[index] !== "`") continue;
            let count = 1;
            while (content[index + count] === "`") count++;
            if (!inlineTicks) inlineTicks = count;
            else if (count === inlineTicks) inlineTicks = 0;
            index += count - 1;
        }
    }
    return !fence && !inlineTicks && !/^(?: {4}|\t)/.test(lines.at(-1));
}

export function emojiStrategy() {
    return {
        id: "emoji",
        match: /(^|[\s([{]):([a-z0-9_+\-]*):?$/i,
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
