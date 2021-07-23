import EasyMDE from "easymde";

function loadEditor(element) {
    const easyMDE = new EasyMDE({
        autoDownloadFontAwesome: false,
        element: element,
        autoRefresh: true,
        spellChecker: false,
        sideBySideFullscreen: false,
        status: false
    });
}

const editors = document.querySelectorAll(".flaskbb-editor");
for(const e of editors) {
    loadEditor(e);
}
