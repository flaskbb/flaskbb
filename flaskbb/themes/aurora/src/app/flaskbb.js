/**
 * flaskbb.js
 * Copyright: (C) 2015 - FlaskBB Team
 * License: BSD - See LICENSE for more details.
 */
import { Modal } from "bootstrap";
import htmx from "htmx.org";
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

    const attachmentToken = () => crypto.randomUUID().split("-").join("");

    const selectedAttachments = (container) => {
        const attachments = [];
        for (const input of container.querySelectorAll('input[type="file"]')) {
            const serializedTokens = input.dataset.attachmentTokens;
            let tokens = serializedTokens ? serializedTokens.split(",") : [];
            if (tokens.length !== input.files.length) {
                tokens = Array.from(input.files, attachmentToken);
                input.dataset.attachmentTokens = tokens.join(",");
            }
            Array.from(input.files).forEach((file, index) => {
                attachments.push({ file, input, index, token: tokens[index] });
            });
        }
        return attachments;
    };

    const syncSelectedAttachments = (container) => {
        const attachments = selectedAttachments(container);
        const form = container.closest("form");
        form.elements.new_attachment_tokens.value = attachments.map(({ token }) => token).join(",");

        const list = container.querySelector(".selected-attachments");
        list.replaceChildren();
        for (const { file, input, index, token } of attachments) {
            const row = document.createElement("div");
            row.className = "attachment-row";

            const icon = document.createElement("span");
            icon.className = "fas fa-paperclip";
            icon.setAttribute("aria-hidden", "true");

            const name = document.createElement("span");
            name.className = "attachment-name";
            name.textContent = `${file.name} (${formatFileSize(file.size)})`;

            const actions = document.createElement("div");
            actions.className = "attachment-actions";

            const insert = document.createElement("button");
            insert.type = "button";
            insert.className = "btn btn-sm btn-outline-secondary insert-attachment";
            insert.dataset.attachmentReference = `attachment:${token}`;
            insert.dataset.attachmentFilename = file.name;
            insert.dataset.attachmentImage = file.type.startsWith("image/") ? "true" : "false";
            insert.textContent = container.dataset.insertLabel;

            const remove = document.createElement("button");
            remove.type = "button";
            remove.className = "btn btn-sm btn-link text-danger remove-attachment";
            remove.textContent = container.dataset.removeLabel;
            remove.addEventListener("click", () => {
                const transfer = new DataTransfer();
                const tokens = input.dataset.attachmentTokens.split(",");
                Array.from(input.files).forEach((candidate, candidateIndex) => {
                    if (candidateIndex !== index) transfer.items.add(candidate);
                });
                input.files = transfer.files;
                input.dataset.attachmentTokens = tokens
                    .filter((_candidate, candidateIndex) => candidateIndex !== index)
                    .join(",");
                syncSelectedAttachments(container);
            });

            actions.append(insert, remove);
            row.append(icon, name, actions);
            list.append(row);
        }
    };

    const formatFileSize = (bytes) => {
        if (bytes < 1024) return `${bytes} B`;
        const units = ["KB", "MB", "GB"];
        let value = bytes / 1024;
        let unit = units[0];
        for (let index = 1; value >= 1024 && index < units.length; index++) {
            value /= 1024;
            unit = units[index];
        }
        return `${value.toFixed(value < 10 ? 1 : 0)} ${unit}`;
    };

    const markdownLabel = (filename) => {
        let escaped = "";
        for (let index = 0; index < filename.length; index++) {
            const character = filename[index];
            if (character === "\\" || character === "[" || character === "]") escaped += "\\";
            escaped += character;
        }
        return escaped;
    };

    document.addEventListener("click", (event) => {
        const button = event.target.closest(".insert-attachment");
        if (!button) return;

        const editor = button.closest("form").querySelector(".flaskbb-editor");
        const label = markdownLabel(button.dataset.attachmentFilename);
        const reference = button.dataset.attachmentReference;
        const markdown =
            button.dataset.attachmentImage === "true"
                ? `![${label}](${reference})`
                : `[${label}](${reference})`;

        editor.focus();
        editor.setRangeText(markdown, editor.selectionStart, editor.selectionEnd, "end");
        editor.dispatchEvent(new Event("input", { bubbles: true }));
    });

    document.querySelectorAll(".attachment-fields").forEach(syncSelectedAttachments);

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

        syncSelectedAttachments(container);

        if (!isFileInput || event.target.files.length === 0) return;
        if (slots <= 0) return;

        const inputs = container.querySelectorAll('input[type="file"]');
        if (Array.from(inputs).some((el) => el.files.length === 0)) return;

        const fresh = event.target.cloneNode();
        fresh.value = "";
        fresh.removeAttribute("id");
        fresh.removeAttribute("data-attachment-tokens");
        fresh.classList.remove("is-invalid");
        fresh.classList.add("mt-2");
        event.target.after(fresh);
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
