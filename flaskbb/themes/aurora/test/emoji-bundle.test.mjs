import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import { JSDOM, requestInterceptor, VirtualConsole } from "jsdom";

test("production bundle renders consistent artwork and manages HTMX editors", { timeout: 5000 }, async () => {
    const requests = [];
    const errors = [];
    let initialized;
    const ready = new Promise((resolve) => { initialized = resolve; });
    const assets = requestInterceptor(async ({ url }) => {
        requests.push(url);
        if (url.startsWith("https://forum.example/prefix/static/")) {
            const content = await readFile(new URL(`../static/${url.split("/").at(-1)}`, import.meta.url));
            return new Response(content, { headers: { "Content-Type": "application/javascript" } });
        }
        return new Response(null, { status: 404 });
    });
    const console = new VirtualConsole();
    console.on("jsdomError", (error) => errors.push(error.message));
    const dom = new JSDOM(`<!doctype html><body data-emoji-base="/prefix/emoji/">
        <div class="post-content">😄 <code>👍</code></div>
        <button type="button" class="emoji-picker-btn" data-editor="content">Emoji</button>
        <textarea id="content" class="flaskbb-editor"></textarea>
        <div class="modal" id="emoji-picker" tabindex="-1">
            <div class="modal-dialog"><div class="modal-content">
                <button type="button" data-bs-dismiss="modal">Close</button>
                <input type="search" id="emoji-search">
                <div class="emoji-picker-results"></div>
                <p class="emoji-picker-empty" hidden>No emojis found.</p>
            </div></div>
        </div>
        <script src="/prefix/static/vendors.js"></script>
        <script src="/prefix/static/app.js"></script></body>`, {
        url: "https://forum.example/prefix/",
        runScripts: "dangerously",
        resources: { interceptors: [assets] },
        virtualConsole: console,
        beforeParse(window) {
            window.document.addEventListener("htmx:load", initialized, { once: true });
            window.document.execCommand = () => false;
            const evaluate = window.XPathExpression.prototype.evaluate;
            window.XPathExpression.prototype.evaluate = function (context, type = 0, result = null) {
                return evaluate.call(this, context, type, result);
            };
        },
    });
    try {
        await new Promise((resolve) => dom.window.addEventListener("load", resolve));
        await ready;
        const { document, htmx } = dom.window;
        assert.deepEqual(errors, []);
        assert.equal(document.querySelector(".post-content img").alt, "😄");
        assert.equal(document.querySelector(".post-content img").src, "https://forum.example/prefix/emoji/1f604.svg");
        assert.equal(document.querySelector("code").textContent, "👍");
        assert.ok(!requests.some((url) => url.includes("emoji-catalog")));
        assert.equal(document.querySelectorAll(".textcomplete-dropdown").length, 1);
        const editor = document.querySelector("textarea");
        htmx.trigger(editor, "htmx:load", { elt: editor });
        assert.equal(document.querySelectorAll(".textcomplete-dropdown").length, 1);
        editor.value = ":smile";
        editor.setSelectionRange(editor.value.length, editor.value.length);
        const rendered = new Promise((resolve) => {
            const observer = new dom.window.MutationObserver(() => {
                if (document.querySelector(".textcomplete-item img")) {
                    observer.disconnect();
                    resolve();
                }
            });
            observer.observe(document.body, { childList: true, subtree: true });
        });
        editor.dispatchEvent(new dom.window.Event("input"));
        await rendered;
        assert.equal(requests.filter((url) => url.includes("emoji-catalog")).length, 0);
        editor.dispatchEvent(new dom.window.KeyboardEvent("keydown", { keyCode: 13 }));
        assert.equal(editor.value, "😄 ");
        const opener = document.querySelector(".emoji-picker-btn");
        const picker = document.getElementById("emoji-picker");
        const search = document.getElementById("emoji-search");
        editor.value = "before selected after";
        editor.setSelectionRange(7, 15);
        let inputs = 0;
        editor.addEventListener("input", () => inputs++);
        opener.click();
        assert.equal(document.activeElement, search);
        assert.equal(picker.querySelectorAll("button[data-emoji]").length, 24);
        assert.ok([...picker.querySelectorAll("img")].every((image) => image.src.startsWith("https://forum.example/prefix/emoji/")));
        search.value = "no_such_emoji";
        search.dispatchEvent(new dom.window.Event("input", { bubbles: true }));
        assert.equal(picker.querySelector(".emoji-picker-empty").hidden, false);
        search.value = "thumbsup";
        search.dispatchEvent(new dom.window.Event("input", { bubbles: true }));
        picker.querySelector("button[data-emoji] img").click();
        assert.equal(editor.value, "before 👍 after");
        assert.equal(editor.selectionStart, 9);
        assert.equal(document.activeElement, editor);
        assert.equal(inputs, 1);
        assert.equal(picker.classList.contains("show"), false);
        opener.click();
        assert.equal(search.value, "");
        search.dispatchEvent(new dom.window.KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
        assert.equal(editor.value, "before 👍 after");
        assert.equal(document.activeElement, editor);
        opener.classList.add("disabled");
        opener.click();
        assert.equal(picker.classList.contains("show"), false);
        opener.classList.remove("disabled");
        opener.click();
        htmx.trigger(editor, "htmx:beforeCleanupElement", { elt: editor });
        assert.equal(document.querySelector(".textcomplete-dropdown"), null);
        assert.equal(document.querySelector(".modal-backdrop"), null);
        editor.remove();
        const replacement = document.createElement("textarea");
        replacement.className = "flaskbb-editor";
        replacement.id = "content";
        document.body.append(replacement);
        htmx.trigger(replacement, "htmx:load", { elt: replacement });
        assert.equal(document.querySelectorAll(".textcomplete-dropdown").length, 1);
        opener.click();
        assert.deepEqual(errors, []);
        const firstChoice = picker.querySelector("button[data-emoji]");
        assert.equal(firstChoice.dataset.emoji, "😄");
        firstChoice.click();
        assert.equal(replacement.value, "😄");
        assert.equal(document.activeElement, replacement);
        assert.ok(requests.every((url) => url.startsWith("https://forum.example/")));
        assert.deepEqual(errors, []);
    } finally {
        dom.window.close();
    }
});
