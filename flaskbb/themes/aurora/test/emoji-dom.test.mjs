import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { afterEach, test } from "node:test";
import { JSDOM } from "jsdom";
import { emojiStrategy, renderEmoji } from "../src/app/emoji.js";
import keywords from "emojilib" with { type: "json" };

const require = createRequire(import.meta.url);
let dom;
page("");
const { Textcomplete } = require("@textcomplete/core");
const { TextareaEditor } = require("@textcomplete/textarea");
dom.window.close();

function page(html) {
    dom = new JSDOM(html, { url: "https://forum.example/" });
    dom.window.document.body.dataset.emojiBase =
        "https://cdn.jsdelivr.net/gh/jdecked/twemoji@17.0.3/assets/svg/";
    for (const key of [
        "window",
        "document",
        "NodeFilter",
        "Image",
        "CustomEvent",
        "getComputedStyle",
        "localStorage",
        "HTMLTextAreaElement",
    ]) {
        Object.defineProperty(globalThis, key, { configurable: true, value: dom.window[key] });
    }
    dom.window.document.execCommand = () => false;
    return dom.window.document;
}

afterEach(() => dom?.window.close());

test("page rendering uses one artwork set and preserves code, links, and inputs", () => {
    const doc = page(`<div id="outside">😄</div><div class="post-content">
        <p>😄 <a href="/user/1">👍🏽</a></p><code>😄</code><pre>😄</pre>
        <textarea>😄</textarea><span contenteditable>😄</span>
        </div><div class="post-signature">❤️</div><div data-emoji>🇦🇹</div>`);
    const link = doc.querySelector("a");
    let clicked = false;
    link.addEventListener("click", () => {
        clicked = true;
    });
    renderEmoji(doc.body);
    assert.equal(doc.querySelectorAll("img.emoji").length, 5);
    for (const selector of ["code", "pre", "textarea", "[contenteditable]"]) {
        assert.equal(doc.querySelector(selector).textContent, "😄");
    }
    assert.equal(doc.querySelector("a"), link);
    link.dispatchEvent(new dom.window.Event("click"));
    assert.ok(clicked);
    const image = doc.querySelector("img");
    assert.equal(image.alt, "😄");
    assert.equal(
        image.src,
        "https://cdn.jsdelivr.net/gh/jdecked/twemoji@17.0.3/assets/svg/1f604.svg",
    );
    assert.equal(image.draggable, false);
    renderEmoji(doc.body);
    assert.equal(doc.querySelectorAll("img.emoji").length, 5);
});

test("HTMX fragment roots inside content are rendered, including preview roots", () => {
    const doc = page('<div class="post-content"><p>😄</p></div><div class="preview">👍</div>');
    renderEmoji(doc.querySelector("p"));
    renderEmoji(doc.querySelector(".preview"));
    assert.equal(doc.querySelectorAll("img.emoji").length, 2);
});

test("local artwork is used in content, previews, and completions without a CDN fallback", () => {
    const doc = page(
        '<div class="post-content">😄</div><div class="preview">👍</div><div id="completion"></div>',
    );
    doc.body.dataset.emojiBase = "/prefix/static/emoji";
    renderEmoji(doc.body);
    doc.querySelector("#completion").innerHTML = emojiStrategy().template({
        character: "😄",
        name: "smile",
    });
    for (const image of doc.querySelectorAll("img")) {
        assert.ok(image.src.startsWith("https://forum.example/prefix/static/emoji/"));
        image.dispatchEvent(new dom.window.Event("error"));
    }
    assert.equal(doc.querySelector("img"), null);
    assert.equal(doc.querySelector(".post-content").textContent, "[emoji]");
});

test("text presentation and copyright symbols stay text", () => {
    const doc = page('<div class="post-content">© ® ™ ☺︎</div>');
    renderEmoji(doc.body);
    assert.equal(doc.querySelector("img"), null);
    assert.equal(doc.querySelector("div").textContent, "© ® ™ ☺︎");
});

test("failed images never switch to the system emoji font", () => {
    const doc = page('<body><div class="message-content">👍🏽</div></body>');
    renderEmoji(doc.body);
    const image = doc.querySelector("img");
    assert.equal(
        image.src,
        "https://cdn.jsdelivr.net/gh/jdecked/twemoji@17.0.3/assets/svg/1f44d-1f3fd.svg",
    );
    image.dispatchEvent(new dom.window.Event("error"));
    assert.equal(doc.querySelector(".message-content").textContent, "[emoji]");
    assert.equal(doc.querySelector("img"), null);
});

test("keyword catalog and skin-tone sequences render as complete images", () => {
    const doc = page("<div></div>");
    const element = doc.querySelector("div");
    for (const character of [
        ...Object.keys(keywords),
        "👍🏽",
        "👩🏿‍💻",
        "🫱🏻‍🫲🏿",
        "🇦🇹",
        "❤️",
        "🏳️‍🌈",
        "👨‍👩‍👧‍👦",
    ]) {
        element.textContent = character;
        renderEmoji(element);
        assert.equal(element.childNodes.length, 1, character);
        assert.equal(element.firstChild.nodeName, "IMG", character);
        assert.equal(element.firstChild.alt, character, character);
    }
});

test("completion templates escape labels and render artwork", () => {
    const doc = page("<div></div>");
    doc.querySelector("div").innerHTML = emojiStrategy().template({
        character: "😄",
        name: '<img src=x onerror="alert(1)">',
    });
    assert.equal(doc.querySelectorAll("img").length, 1);
    assert.ok(doc.querySelector("div").textContent.includes("<img src=x"));
});

test("eye-in-speech-bubble variants use the fork's artwork filename", () => {
    const doc = page("<div></div>");
    const element = doc.querySelector("div");
    for (const character of ["👁️‍🗨️", "👁️‍🗨", "👁‍🗨️", "👁‍🗨"]) {
        element.textContent = character;
        renderEmoji(element);
        assert.equal(element.childNodes.length, 1);
        assert.equal(element.firstChild.alt, character);
        assert.ok(element.firstChild.src.endsWith("/svg/1f441-200d-1f5e8.svg"));
    }
});

test("autocomplete inserts Unicode and removes its dropdown", { timeout: 3000 }, async () => {
    const doc = page("<textarea>:thumbsup</textarea>");
    const textarea = doc.querySelector("textarea");
    textarea.setSelectionRange(textarea.value.length, textarea.value.length);
    const completion = new Textcomplete(new TextareaEditor(textarea), [emojiStrategy()]);
    await new Promise((resolve) => {
        completion.once("rendered", resolve);
        completion.trigger(textarea.value);
    });
    assert.ok(completion.dropdown.el.querySelector("img.emoji"));
    completion.dropdown.select(completion.dropdown.items[0]);
    assert.equal(textarea.value, "👍 ");
    completion.destroy();
    assert.equal(doc.querySelector(".textcomplete-dropdown"), null);
});
