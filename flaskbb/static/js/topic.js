/**
 * Topic.js
 */
$(document).ready(function () {
        $(".quote_btn").click(function (event) {
            event.preventDefault();

            // QuickReply Textarea
            var $contents = $(".reply-content textarea#content");
            // Original Post
            var $original = $(".post_body#" + $(this).attr('data-post-id'));
            // Content of the Post, in plaintext (strips tags) and without the signature
            var content = $original.clone().find('.signature').remove().end().text().trim();

            // Add quote to the Quickreply Textarea
            if ($contents.val().length > 0) {
                $contents.val($contents.val() + "\n[quote]" + content + "[/quote]");
            } else {
        $contents.val("[quote]" + content + "[/quote]");
        }
    });
});
