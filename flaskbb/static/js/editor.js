/* This file just holds some configuration values for the editor */
marked.setOptions({
    gfm: true,
    tables: true,
    breaks: true,
    pedantic: false,
    sanitize: true,
    smartLists: true,
    smartypants: false
});

$(".flaskbb-editor").markdown({
    iconlibrary: "fa",
    additionalButtons: [
        [{
            name: "groupHelp",
            data: [{
                name: "cmdHelp",
                toggle: false, // this param only take effect if you load bootstrap.js
                title: "Help",
                icon: "fa fa-question",
                btnClass: 'btn btn-success',
                callback: function(e){
                    $('#editor-help').modal('show')
                }
            }]
        }]
    ]
});

$('.flaskbb-editor').textcomplete([
    { // emoji strategy
        match: /\B:([\-+\w]*)$/,
        search: function (term, callback) {
            callback($.map(emojies, function (emoji) {
                return emoji.indexOf(term) === 0 ? emoji : null;
            }));
        },
        template: function (value) {
            return '<img class="emoji" src="/static/emoji/' + value + '.png"></img>' + value;
        },
        replace: function (value) {
            return ':' + value + ': ';
        },
        index: 1
    },
], {
    onKeydown: function (e, commands) {
        if (e.ctrlKey && e.keyCode === 74) { // CTRL-J
            return commands.KEY_ENTER;
        }
    }
});
