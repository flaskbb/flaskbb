import "@flaskbb/markdown-toolbar-element";
import { Modal, Tooltip } from "bootstrap";
import htmx from "htmx.org";

import "./app/confirm_modal.js";
import "./app/editor.js";
import { initializeEmoji } from "./app/emoji.js";
import { show_management_search } from "./app/flaskbb.js";
import { insertQuote } from "./app/quote.js";

initializeEmoji({ htmx, Modal });

import "./scss/styles.scss";
window.app = { show_management_search, insertQuote };

// htmx has to be reachable via window. plugins register extensions against it and
// templates outside this bundle call into it.
window.htmx = htmx;

// without a history cache htmx keeps no page snapshots, and the CSRF token in
// them, in localStorage. going back to a page htmx navigated to reloads it
htmx.config.historyCacheSize = 0;
htmx.config.refreshOnHistoryMiss = true;

var flaskbbAllowList = Tooltip.Default.allowList;
// allow <time> elements
flaskbbAllowList.time = [];

htmx.onLoad((root) => {
    root.querySelectorAll('[data-bs-toggle="tooltip"], [data-tooltip="tooltip"]').forEach((el) => {
        Tooltip.getOrCreateInstance(el);
    });
});

// a tooltip still open on an element htmx removes would stay on screen. only an
// idle tooltip (no tip element) is disposed right away: disposing one that is
// showing or fading out nulls the instance under its pending transition
// callback, so that one is hidden first and disposed once it is hidden
document.addEventListener("htmx:beforeCleanupElement", (event) => {
    var tooltip = Tooltip.getInstance(event.target);
    if (!tooltip) {
        return;
    }
    if (!tooltip.tip) {
        tooltip.dispose();
        return;
    }
    event.target.addEventListener(
        "hidden.bs.tooltip",
        () => {
            tooltip.dispose();
        },
        { once: true },
    );
    tooltip.hide();
});

document.addEventListener("click", (event) => {
    var toggle = event.target.closest(".tree-toggle");
    if (!toggle) {
        return;
    }
    event.preventDefault();
    var parent = toggle.closest(".tree-parent");
    var expanded = parent.classList.toggle("expanded");
    toggle.setAttribute("aria-expanded", expanded ? "true" : "false");
});
