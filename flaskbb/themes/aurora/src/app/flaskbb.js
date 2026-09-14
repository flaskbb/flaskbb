/**
 * flaskbb.js
 * Copyright: (C) 2015 - FlaskBB Team
 * License: BSD - See LICENSE for more details.
 */
import { Modal } from "bootstrap";
import htmx from "htmx.org";
import twemoji from "twemoji";
import { isHidden } from "./utils";


export function show_management_search() {
    let form = document.querySelector(".search-form");

    if (isHidden(form)) {
        form.style.display = "block";
        form.querySelector("input").focus();
    } else {
        form.style.display = "none";
    }
}

// content htmx swaps into a modal, like the report form, opens that modal
document.addEventListener("htmx:afterSwap", (event) => {
    const modal = event.detail.target.closest(".modal");
    if (modal) {
        Modal.getOrCreateInstance(modal).show();
    }
});


export function parse_emoji(value) {
    // use this instead of twemoji.parse
    return twemoji.parse(value, {
        callback: function (icon, options, variant) {
            // exclude some characters
            switch (icon) {
                case "a9": // © copyright
                case "ae": // ® registered trademark
                case "2122": // ™ trademark
                    return false;
            }
            return "".concat(
                options.base,
                options.size,
                "/",
                icon,
                options.ext
            );
        },
        // use svg instead of the default png
        folder: "svg",
        ext: ".svg",
    });
}

document.addEventListener("DOMContentLoaded", function (_event) {
    // attachment inputs: once an input has a file, offer another (empty)
    // input so more files can be picked from a different location, and
    // reject picks that are too big or would exceed the per-post attachment
    // limit before the form is ever submitted. Delegated so it also fires on
    // the inputs added here and on the delete checkboxes that free up slots
    // again.
    const dropOversizedFiles = (input, container) => {
        const maxSize = parseInt(container.dataset.maxSize, 10) || 0;
        if (!maxSize) return false;

        const kept = new DataTransfer();
        for (const file of input.files) {
            if (file.size <= maxSize) kept.items.add(file);
        }
        if (kept.files.length === input.files.length) return false;

        // keep the files that do fit, so only the offending ones are lost
        input.files = kept.files;
        return true;
    };

    const attachmentSlotsLeft = (container) => {
        const max = parseInt(container.dataset.maxAttachments, 10) || 0;
        if (!max) return Infinity;

        const existing = parseInt(container.dataset.existingAttachments, 10) || 0;
        const form = container.closest("form");
        const deleted = form
            ? form.querySelectorAll('input[name="delete_attachments"]:checked').length
            : 0;
        const selected = Array.from(
            container.querySelectorAll('input[type="file"]')
        ).reduce((n, el) => n + el.files.length, 0);
        return max - (existing - deleted) - selected;
    };

    document.addEventListener("change", (event) => {
        const form = event.target.closest("form");
        const container = form && form.querySelector(".attachment-fields");
        if (!container) return;

        const isFileInput = event.target.matches(
            '.attachment-fields input[type="file"]'
        );
        const isDeleteCheckbox = event.target.matches(
            'input[name="delete_attachments"]'
        );
        if (!isFileInput && !isDeleteCheckbox) return;

        const error = container.querySelector(".attachment-limit-error");
        const sizeError = container.querySelector(".attachment-size-error");
        let rejected = false;

        if (isFileInput && event.target.files.length > 0) {
            const tooLarge = dropOversizedFiles(event.target, container);
            sizeError.style.display = tooLarge ? "block" : "none";
        }

        if (isFileInput && attachmentSlotsLeft(container) < 0) {
            // this pick went over the limit - drop it and tell the user
            event.target.value = "";
            rejected = true;
        }
        const slots = attachmentSlotsLeft(container);
        error.style.display = rejected || slots < 0 ? "block" : "none";

        if (!isFileInput || event.target.files.length === 0) return;
        if (slots <= 0) return;

        const inputs = container.querySelectorAll('input[type="file"]');
        if (Array.from(inputs).some((el) => el.files.length === 0)) return;

        const fresh = event.target.cloneNode();
        fresh.value = "";
        fresh.removeAttribute("id");
        fresh.classList.remove("is-invalid");
        fresh.classList.add("mt-2");
        event.target.after(fresh);
    });

    // Reply to post. delegated, so it keeps working on posts htmx swapped in
    document.addEventListener("click", (event) => {
        const button = event.target.closest(".quote-btn");
        if (!button) return;
        event.preventDefault();
        const post_id = button.dataset.postId;
        const urlprefix =
            typeof FORUM_URL_PREFIX !== 'undefined'
                ? FORUM_URL_PREFIX
                : "";
        const url = `${urlprefix}/post/${post_id}/raw`;

        const editor = document.querySelector(".flaskbb-editor");
        fetch(url)
            .then((response) => response.text())
            .then((data) => {
                editor.value = data;
                editor.selectionStart = editor.selectionEnd =
                    editor.value.length;
                editor.scrollTop = editor.scrollHeight;
                window.location.href = "#content";
            })
            .catch((error) => {
                console.error("something bad happened", error);
            });
    });

    // listen on the action-checkall checkbox to un/check all. delegated, so it
    // keeps working on lists htmx swapped in
    document.addEventListener("change", (event) => {
        if (!event.target.matches(".action-checkall")) return;
        document.querySelectorAll("input.action-checkbox").forEach((cb) => {
            cb.checked = event.target.checked;
        });
    });

    // a click on a set-checkbox row toggles its checkbox, unless the click was
    // on the checkbox itself. delegated, so it keeps working on lists htmx
    // swapped in
    document.addEventListener("click", (event) => {
        const row = event.target.closest(".set-checkbox");
        if (!row || event.target.matches("input.action-checkbox")) return;
        event.preventDefault();
        const cb = row.querySelector("input.action-checkbox");
        cb.checked = !cb.checked;
    });

});

htmx.onLoad((root) => {
    parse_emoji(root);

    root.querySelectorAll("time").forEach((el) => {
        let date = new Date(el.getAttribute("datetime"));
        const options = {
            weekday: undefined,
            era: undefined,
            year: "numeric",
            month: "short",
            day: "numeric",
            second: undefined,
        };
        if (el.dataset.what_to_display == "date-only") {
            options.hour = undefined;
            options.minute = undefined;
        } else if (el.dataset.what_to_display == "time-only") {
            options.year = undefined;
            options.month = undefined;
            options.day = undefined;
            options.hour = "2-digit";
            options.minute = "2-digit";
        } else {
            options.hour = "2-digit";
            options.minute = "2-digit";
        }
        el.textContent = date.toLocaleString(undefined, options);
    });
});
