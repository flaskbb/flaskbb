/**
 * topic.js
 */
$(document).ready(function () {
    // Quote
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
});
