import keywords from "emojilib" with { type: "json" };
import aliases from "./aliases.json" with { type: "json" };

const emojis = Object.entries(keywords).map(([character, names]) => ({
    character,
    name: names[0],
    aliases: aliases[character] || [],
    keywords: names,
}));

export const commonEmoji = "😄 😂 😉 😊 😍 😎 🤔 😢 😭 😱 😡 😅 👍 👎 👋 👏 🙏 💪 ❤️ 💔 🎉 🔥 💯 ☕"
    .split(" ").map((character) => emojis.find((emoji) => emoji.character === character));

export function searchEmoji(term, limit = 5) {
    const query = term.toLowerCase().replace(/\s+/g, "_").replace(/(\w)-(?=\w)/g, "$1_");
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
        if (emoji.aliases.some((name) => name.includes(query)) ||
            emoji.keywords.some((name) => name.includes(query))) {
            matches.push(emoji);
        }
    }
    return matches;
}
