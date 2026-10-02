import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { test } from "node:test";
import { emojiContext, emojiStrategy, searchEmoji } from "../src/app/emoji.js";

const require = createRequire(import.meta.url);
const { Strategy } = require("@textcomplete/core/dist/Strategy");
const { SearchResult } = require("@textcomplete/core/dist/SearchResult");

test("names and familiar aliases resolve before keyword matches", () => {
    assert.equal(searchEmoji("smile")[0].character, "😄");
    assert.equal(searchEmoji("thumbsup")[0].character, "👍");
    assert.equal(searchEmoji("+1")[0].character, "👍");
    assert.equal(searchEmoji("-1")[0].character, "👎");
    assert.equal(searchEmoji("grinning_face")[0].character, "😀");
    assert.deepEqual(searchEmoji("grinning face"), searchEmoji("grinning_face"));
    assert.deepEqual(searchEmoji("grinning-face"), searchEmoji("grinning_face"));
    assert.equal(searchEmoji("party_popper")[0].character, "🎉");
    assert.equal(searchEmoji("SMILE")[0].character, "😄");
    assert.ok(searchEmoji("happy").length);
    assert.equal(searchEmoji("").length, 5);
    assert.equal(searchEmoji("", 48).length, 48);
    assert.deepEqual(searchEmoji("smile", 1), searchEmoji("smile").slice(0, 1));
    assert.deepEqual(searchEmoji("smile", 0), []);
    assert.deepEqual(searchEmoji("this_emoji_does_not_exist"), []);
});

test("emoji triggers require a boundary and preserve it during insertion", () => {
    const strategy = new Strategy(emojiStrategy());
    const emoji = searchEmoji("smile")[0];
    for (const text of [":smile", "hello :smile", "(:smile", "[:smile", "\n:smile:"]) {
        const match = strategy.matchWithContext(text);
        assert.equal(match[2], "smile");
        const result = new SearchResult(emoji, "smile", strategy);
        assert.deepEqual(result.replace(text, "after"), [
            `${text.slice(0, text.indexOf(":"))}😄 `,
            "after",
        ]);
    }
    for (const text of ["https:", "https://host/:smile", "12:30", "word:smile", "\\:smile"]) {
        assert.equal(strategy.matchWithContext(text), null, text);
    }
});

test("completion stays out of Markdown code, including escaped and nested backticks", () => {
    for (const text of [
        "`:smile",
        "``text ` :smile",
        "```python\n:smile",
        "~~~\n:smile",
        "````\n```\n:smile",
        "> ```\n> :smile",
        "    :smile",
        "\t:smile",
    ]) {
        assert.equal(emojiContext(text), false, text);
    }
    for (const text of [
        "`done` :smile",
        "``a ` b`` :smile",
        "\\` :smile",
        "```\ncode\n```\n:smile",
        "~~~\ncode\n~~~\n:smile",
        "> ```\n> code\n> ```\n:smile",
    ]) {
        assert.equal(emojiContext(text), true, text);
    }
});
