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
    ],
    onPreview: function(e) {
        return parse_emoji(marked(e.getContent()));
    }
});

$('.flaskbb-editor').textcomplete([
    { // emoji strategy
        match: /\B:([\-+\w]*)$/,
        search: function (term, callback) {
            callback($.map(emojies, function (value) {
                return value[0].indexOf(term) !== -1 ? {character: value[1], name: value[0]} : null;
            }));
        },
        template: function (value) {
            return parse_emoji(value.character) + ' ' + value.name;
        },
        replace: function (value) {
            return value.character + ' ';
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
