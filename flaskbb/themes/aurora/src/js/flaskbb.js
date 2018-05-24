/**
 * flaskbb.js
 * Copyright: (C) 2015 - FlaskBB Team
 * License: BSD - See LICENSE for more details.
 */


 // get the csrf token from the header
var csrftoken = $('meta[name=csrf-token]').attr('content');

var show_management_search = function() {
    var body = $('.management-body');
    var form = body.find('.search-form');

    // toggle
    form.slideToggle(function() {
        if(form.css('display') != 'none') {
            //body.css('padding', '15px');
            form.find('input').focus();
        }
    });
};

var flash_message = function(message) {
    var container = $('#flashed-messages');

    var flashed_message = '<div class="alert alert-'+ message.category +'">';

    if(message.category == 'success') {
        flashed_message += '<span class="glyphicon glyphicon-ok-sign"></span>&nbsp;';
    } else if (message.category == 'error') {
        flashed_message += '<span class="glyphicon glyphicon-exclamation-sign"></span>&nbsp;';
    } else {
        flashed_message += '<span class="glyphicon glyphicon-info-sign"></span>&nbsp;';
    }
    flashed_message += '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button>' + message.message + '</div>';
    container.append(flashed_message);
};

var BulkActions = function() {
    this.execute = function(endpoint) {
        var selected = $('input.action-checkbox:checked').length;
        var data = {"ids": []};

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

    this.confirm = function(endpoint, data) {
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

var send_data = function(endpoint_url, data) {
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
            var form = $('#' + v.type + '-' + v.id);

            // check if there is something to reverse it, otherwise remove the DOM.
            if(v.reverse) {
                form.attr('action', v.reverse_url);
                if(v.type == 'ban') {
                    reverse_html = '<span class="fa fa-flag text-success" data-toggle="tooltip" data-placement="top" title="'+ v.reverse_name +'"></span>';
                } else if (v.type == 'unban') {
                    reverse_html = '<span class="fa fa-flag text-warning" data-toggle="tooltip" data-placement="top" title="'+ v.reverse_name +'"></span>';
                }
                form.find('button').html(reverse_html);
            } else if(v.type == "delete") {
                form.parents(".row").remove();
            }

        });
    })
    .fail(function(error) {
        flash_message(error);
    });
};

var parse_emoji = function(value) {
    // use this instead of twemoji.parse
    return twemoji.parse(
        value,
        {
            callback: function(icon, options, variant) {
                // exclude some characters
                switch ( icon ) {
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

$(document).ready(function () {
    // listen on the action-checkall checkbox to un/check all
    $('.action-checkall').change(function() {
        $('input.action-checkbox').prop('checked', this.checked);
    });

    // Reply to post
    $('.quote-btn').click(function (event) {
        event.preventDefault();
        var post_id = $(this).attr('data-post-id');
        var urlprefix = typeof FORUM_URL_PREFIX !== typeof undefined ? FORUM_URL_PREFIX : "";

        $.get(urlprefix + '/post/' + post_id + '/raw', function(text) {
            var $contents = $('.flaskbb-editor');
            $contents.val(($contents.val() + '\n' + text).trim() + '\n');
            $contents.selectionStart = $contents.selectionEnd = $contents.val().length;
            $contents[0].scrollTop = $contents[0].scrollHeight;
            window.location.href = '#content';
        });
    });

    // Triggers the confirm dialog
    $('button[name="confirmDialog"]').on('click', function(e) {
        var $form = $(this).closest('form');
        e.preventDefault();
        $('.confirmModal').modal({ keyboard: true })
            .one('click', '.confirmBtn', function() {
                $form.trigger('submit'); // submit the form
            })
            // .one() is NOT a typo of .on()
            .on('hidden.bs.modal', function () {
                $('.confirmBtn').unbind();
            }
        );
    });

    $('time').each(function(i, elem) {
        var date = new Date(elem.getAttribute('datetime'));

        var options = {
            weekday: undefined,
            era: undefined,
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            second: undefined,
        };
        if (elem.dataset.what_to_display == 'date-only') {
            options.hour = undefined;
            options.minute = undefined;
        } else {
            options.hour = '2-digit';
            options.minute = '2-digit';
        }
        elem.textContent = date.toLocaleString(undefined, options);
    });

    parse_emoji(document.body);
});
