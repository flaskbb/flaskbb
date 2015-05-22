/**
 * flaskbb.js
 * Copyright: (C) 2015 - FlaskBB Team
 * License: BSD - See LICENSE for more details.
 */


 // get the csrf token from the header
var csrftoken = $('meta[name=csrf-token]').attr('content');

var change_link = function(data, link, text) {
    $.each(data, function(k, v) {
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
    this.execute = function(url, confirm_message) {
        var selected = $('input.action-checkbox:checked').size();
        var data = {"ids": []};

        // don't do anything if nothing is selected
        if (selected === 0) {
            return false;
        }

        $('input.action-checkbox:checked').each(function(k, v) {
            data.ids.push($(v).val());
        });

        // http://stackoverflow.com/questions/784929/what-is-the-not-not-operator-in-javascript
        if(!!confirm_message) {
            if(!confirm(confirm_message)) {
                return false;
            }
        }

        send_data(url, data)

        return false;
    };

    $(function() {
        $('.action-checkall').change(function() {
            $('input.action-checkbox').prop('checked', this.checked);
        });
    });
};

var send_data = function(endpoint_url, data) {
    $.ajax({
        url: BASE_URL + endpoint_url,
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
                form.find('button').html(v.reverse_name);
            } else {
                form.parents('.action-row').remove();
            }

        });
    })
    .fail(function(error) {
        flash_message(error);
    });
};

$(document).ready(function () {
    // TODO: Refactor
    // Reply conversation
    $('.reply-btn').click(function (event) {
        event.preventDefault();
        var message_id = $(this).attr('data-message-id');

        $.get('/message/message/' + message_id + '/raw', function(text) {
            var $contents = $('.message-content .md-editor textarea');
            $contents.val(($contents.val() + '\n' + text).trim() + '\n');
            $contents.selectionStart = $contents.selectionEnd = $contents.val().length;
            $contents[0].scrollTop = $contents[0].scrollHeight;
            window.location.href = '#content';
        });
    });
    // Reply to post
    $('.quote_btn').click(function (event) {
        event.preventDefault();
        var post_id = $(this).attr('data-post-id');

        $.get('/post/' + post_id + '/raw', function(text) {
            var $contents = $('.reply-content .md-editor textarea');
            console.log($contents);
            $contents.val(($contents.val() + '\n' + text).trim() + '\n');
            $contents.selectionStart = $contents.selectionEnd = $contents.val().length;
            $contents[0].scrollTop = $contents[0].scrollHeight;
            window.location.href = '#content';
        });
    });
});
