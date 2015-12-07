/* This file just holds some configuration values for the editor */

$(".flaskbb-editor").markdown({
    iconlibrary: "fa",
    hiddenButtons: "cmdPreview",
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
        },{
            name: 'groupPreview',
            data: [{
                name: 'cmdNewPreview',
                toggle: true,
                hotkey: 'Ctrl+P',
                title: 'Preview',
                btnText: 'Preview',
                btnClass: 'btn btn-primary btn-sm',
                icon: 'fa fa-search',
                callback: function(e){
                    // Check the preview mode and toggle based on this flag
                    var isPreview = e.$isPreview,content;

                    if (isPreview === false) {
                      // Give flag that tell the editor enter preview mode
                      e.showPreview();
                      e.enableButtons('cmdNewPreview');
                    } else {
                      e.hidePreview();
                    }
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
