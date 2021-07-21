/**
 * flaskbb.js
 * Copyright: (C) 2015 - FlaskBB Team
 * License: BSD - See LICENSE for more details.
 */
import { $ } from 'jquery';

// get the csrf token from the header
let csrf_token = document.querySelector('meta[name=csrf-token]').content

export function show_management_search() {
    let form = document.querySelector('.search-form');

    if (window.getComputedStyle(form).display === "none") {
        form.style.display = "block";
        form.querySelector('input').focus();
    } else {
        form.style.display = "none";
    }
};

function flash_message(message) {
    let container = document.getElementById("flashed-messages");

    let flashed_message = '<div class="alert alert-' + message.category + '">';

    if (message.category == 'success') {
        flashed_message += '<span class="fas fa-ok-sign"></span>&nbsp;';
    } else if (message.category == 'error') {
        flashed_message += '<span class="fas fa-exclamation-sign"></span>&nbsp;';
    } else {
        flashed_message += '<span class="fas fa-info-sign"></span>&nbsp;';
    }
    flashed_message += '<button type="button" class="close" data-dismiss="alert">&times;</button>' + message.message + '</div>';
    container.insertAdjacentText('beforeend', flashed_message);
};

export class BulkActions {
    execute(endpoint) {
        let selected = $('input.action-checkbox:checked').length;
        let data = { "ids": [] };

        // don't do anything if nothing is selected
        if (selected === 0) {
            return false;
        }

        $('input.action-checkbox:checked').each(function(k, v) {
            data.ids.push($(v).val());
        });

        this.confirm(endpoint, data);
        return false;
    };

    confirm(endpoint, data) {
        $('.confirmModal').modal({ keyboard: false })
            .one('click', '.confirmBtn', function() {
                $('.confirmModal').modal('hide');
                send_data(endpoint, data);
            })
            .on('hidden.bs.modal', function() {
                $('.confirmBtn').unbind();
            }
            );
    };
};

export function send_data(endpoint_url, data) {
    $.ajax({
        url: endpoint_url,
        method: "POST",
        data: JSON.stringify(data),
        dataType: "json",
        contentType: "application/json",
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    })
        .done(function(response) {
            flash_message(response);
            $.each(response.data, function(k, v) {
                // get the form
                let form = $('#' + v.type + '-' + v.id);

                // check if there is something to reverse it, otherwise remove the DOM.
                if (v.reverse) {
                    form.attr('action', v.reverse_url);
                    if (v.type == 'ban') {
                        reverse_html = '<span class="fa fa-flag text-success" data-toggle="tooltip" data-placement="top" title="' + v.reverse_name + '"></span>';
                    } else if (v.type == 'unban') {
                        reverse_html = '<span class="fa fa-flag text-warning" data-toggle="tooltip" data-placement="top" title="' + v.reverse_name + '"></span>';
                    }
                    form.find('button').html(reverse_html);
                } else if (v.type == "delete") {
                    form.parents(".row").remove();
                }

            });
        })
        .fail(function(error) {
            flash_message(error);
        });
};

export function parse_emoji(value) {
    // use this instead of twemoji.parse
    return twemoji.parse(
        value,
        {
            callback: function(icon, options, variant) {
                // exclude some characters
                switch (icon) {
                    case 'a9':      // © copyright
                    case 'ae':      // ® registered trademark
                    case '2122':    // ™ trademark
                        return false;
                }
                return ''.concat(options.base, options.size, '/', icon, options.ext);
            },
            // use svg instead of the default png
            folder: 'svg',
            ext: '.svg'
        }
    )
};

document.addEventListener("DOMContentLoaded", function(event) {

    // Reply to post
    document.querySelectorAll(".quote-btn").forEach(el => el.addEventListener('click', event => {
        event.preventDefault();
        const post_id = event.target.dataset.postId;
        const urlprefix = typeof FORUM_URL_PREFIX !== typeof undefined ? FORUM_URL_PREFIX : "";
        const url = `${urlprefix}post/${post_id}/raw`;

        const editor = document.querySelector(".flaskbb-editor");
        fetch(url)
            .then(response => response.text())
            .then(data => {
                editor.value = data;
                editor.selectionStart = editor.selectionEnd = editor.value.length;
                editor.scrollTop = editor.scrollHeight;
                window.location.href = '#content';
            })
            .catch(error => {
                console.error("something bad happened", error)
            })
    }));

    // listen on the action-checkall checkbox to un/check all
    document.querySelectorAll(".action-checkall").forEach(el => el.addEventListener('change', event => {
        const cbs = document.querySelectorAll('input.action-checkbox')
        for (var i = 0; i < cbs.length; i++) {
            cbs[i].checked = event.target.checked;
        }
    }));

    document.querySelectorAll("time").forEach(el => {
        let date = new Date(el.getAttribute('datetime'));
        const options = {
            weekday: undefined,
            era: undefined,
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            second: undefined,
        };
        if (el.dataset.what_to_display == 'date-only') {
            options.hour = undefined;
            options.minute = undefined;
        } else {
            options.hour = '2-digit';
            options.minute = '2-digit';
        }
        el.textContent = date.toLocaleString(undefined, options);
    })

    parse_emoji(document.body);
});
