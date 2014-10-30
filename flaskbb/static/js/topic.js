/**
 * topic.js
 */
$(document).ready(function () {
    // Quote
    $('.quote_btn').click(function (event) {
        event.preventDefault();
        var post_id = $(this).attr('data-post-id');

        $.get('/post/' + post_id + '/format_quote', function(text) {
            var $contents = $('.reply-content textarea#content');
            $contents.val(($contents.val() + '\n' + text).trim() + '\n');
            $contents.selectionStart = $contents.selectionEnd = $contents.val().length;
            $contents[0].scrollTop = $contents[0].scrollHeight;
            window.location.href = '#content';
        });
    });
});
