/**
 * flaskbb.js
 * Copyright: (C) 2015 - FlaskBB Team
 * License: BSD - See LICENSE for more details.
 */
import { Modal } from "bootstrap";
import twemoji from "twemoji";
import { isHidden } from "./utils";


// get the csrf token from the header
let csrf_token = document.querySelector("meta[name=csrf-token]").content;

export function show_management_search() {
    let form = document.querySelector(".search-form");

    if (isHidden(form)) {
        form.style.display = "block";
        form.querySelector("input").focus();
    } else {
        form.style.display = "none";
    }
}

function flash_message(message) {
    let container = document.getElementById("flashed-messages");

    let flashed_message = `<div class="alert alert-${message.category} alert-dismissible fade show">`;

    if (message.category === "success") {
        flashed_message += '<span class="fas fa-check me-2"></span>';
    } else if (message.category === "danger" || message.category === "error") {
        flashed_message += '<span class="fas fa-xmark me-2"></span>';
    } else {
        flashed_message += '<span class="fas fa-info me-2"></span>';
    }
    flashed_message += `
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>

        ${message.message}
    </div>`;
    container.insertAdjacentHTML("beforeend", flashed_message);
}

class BaseAction {
    confirm(endpoint, data, callback = undefined) {
        const modalEl = document.getElementById("confirmModal");
        const modal = Modal.getOrCreateInstance(modalEl);
        modal.show();

        const confirmBtn = modalEl.querySelector(".confirmBtn");
        confirmBtn.addEventListener("click", (e) => {
            e.preventDefault();
            modal.hide();
            sendData(endpoint, data, callback);
        }, { once: true });
    }
}

export class Actions {
    execute(endpoint, data, callback = undefined, showConfirm = false) {
        if (!data) {
            return false;
        }

        const action = () => sendData(endpoint, data, callback);
        if (showConfirm) {
            showConfirmModal(action);
        } else {
            action();
        }
        return false;
    }
}

export class BulkActions {
    execute(endpoint) {
        const selected = document.querySelectorAll("input.action-checkbox:checked");
        if (selected.length === 0) return false;

        const data = { ids: Array.from(selected, input => input.value) };
        showConfirmModal(() => sendBulkData(endpoint, data));
        return false;
    }
}

async function makeRequest(endpoint, data) {
    try {
        const response = await fetch(endpoint, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrf_token,
                "Content-Type": "application/json",
            },
            body: JSON.stringify(data),
        });
        const resData = await response.json();
        flash_message(resData);
        return resData;
    } catch (error) {
        console.error("error: ", error);
        flash_message(error);
        return null;
    }
}


function showConfirmModal(onConfirm) {
    const modalEl = document.getElementById("confirmModal");
    const modal = Modal.getOrCreateInstance(modalEl);
    modal.show();

    const confirmBtn = modalEl.querySelector(".confirmBtn");
    // do not add duplicated eventlisteners
    if (confirmBtn.getAttribute('confirmListener') !== 'true') {
        confirmBtn.setAttribute('confirmListener', 'true');
        confirmBtn.addEventListener("click", (e) => {
            e.preventDefault();
            modal.hide();
            onConfirm();
        }, { once: true });
    }
}


export async function sendData(endpoint_url, data, callback) {
    const resData = await makeRequest(endpoint_url, data);
    if (resData && typeof callback === 'function') {
        callback(resData);
    }
}


export async function sendBulkData(endpoint_url, data) {
    const resData = await makeRequest(endpoint_url, data);
    if (!resData?.data) return;

    const iconMap = {
        ban: { color: "text-success", icon: "fa-flag" },
        unban: { color: "text-warning", icon: "fa-flag" }
    };

    for (const obj of resData.data) {
        const form = document.querySelector(`#${obj.type}-${obj.id}`);
        if (!form) continue;

        if (obj.reverse) {
            form.setAttribute("action", obj.reverse_url);

            const config = iconMap[obj.reverse];
            if (config) {
                form.querySelector("button").innerHTML =
                    `<span class="fas ${config.icon} ${config.color}" data-bs-toggle="tooltip" title="${obj.reverse_name}"></span>`;
            }
        } else if (obj.type === "delete") {
            form.closest('tr')?.remove() || form.parentNode.parentNode.remove();
        }
    }
}


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

function celery_not_running_notification(notification) {
    let no_notifications = document.getElementById("overview-no-notifications");
    let notifications = document.querySelector(".overview-notifications");

    // replace the no notifications notice with ours
    if (no_notifications == null) {
        no_notifications.outerHTML = notification;
    } else {
        notifications.innerHTML = notification;
    }
}

export function check_overview_status(endpoint, notification, running, not_running) {
    let celerystatus = document.getElementById("celery-status");
    fetch(endpoint, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
        }
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.celery_running) {
                celerystatus.outerHTML = running;
            } else {
                celerystatus.outerHTML = not_running;
                celery_not_running_notification(notification);
            }
        })
        .catch((error) => {
            flash_message(error);
        });
}

document.addEventListener("DOMContentLoaded", function (event) {
    // Reply to post
    document.querySelectorAll(".quote-btn").forEach((el) =>
        el.addEventListener("click", (event) => {
            event.preventDefault();
            const post_id = event.target.dataset.postId;
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
        })
    );

    // listen on the action-checkall checkbox to un/check all
    document.querySelectorAll(".action-checkall").forEach((el) => {
        el.addEventListener("change", (event) => {
            const cbs = document.querySelectorAll("input.action-checkbox");
            for (var i = 0; i < cbs.length; i++) {
                cbs[i].checked = event.target.checked;
            }
        })
    }
    );

    document.querySelectorAll(".action-checkbox").forEach((el) => {
        el.addEventListener("click", (event) => {
            event.stopPropagation()
        })
    }
    );

    // listen on set-checkbox to check the nearest checkbox
    document.querySelectorAll(".set-checkbox").forEach((el) => {
        el.addEventListener("click", (event) => {
            event.preventDefault();
            const cb = el.querySelector("input.action-checkbox");
            cb.checked = !cb.checked;
        })
    }
    );

    document.querySelectorAll("time").forEach((el) => {
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

    parse_emoji(document.body);
});
