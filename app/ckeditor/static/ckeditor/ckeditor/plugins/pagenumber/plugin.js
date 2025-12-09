/*
Copyright (c) 2025 Xavier Beheydt <xavier.beheydt@gmail.com>
*/

CKEDITOR.plugins.add('pagenumber', {
    init: function (editor) {
        var cur_lang = editor.config.language || CKEDITOR.lang.detect(CKEDITOR.config.defaultLanguage);
        var pagenumber_strings = {
            en: {
                label: "<<Page Number>>",
            },
            fr: {
                label: "<<Numéro Page>>",
            }
        };
        var local_lang = pagenumber_strings[cur_lang] || pagenumber_strings['en'];

        // Command to insert current page number from facsimile viewer
        editor.addCommand('insertPageNumber', {
            exec: function(editor) {
                var pageNumber = null;
                
                // Try to get page number from the facsimile viewer
                if (typeof window.viewerControls !== 'undefined' && window.viewerControls && 
                    window.viewerControls.viewer && typeof window.viewerControls.viewer.currentPage === 'function') {
                    var pageIndex = window.viewerControls.viewer.currentPage(); // 0-based
                    pageNumber = pageIndex + 1; // Convert to 1-based
                } else if (typeof window.viewer !== 'undefined' && window.viewer && 
                           typeof window.viewer.currentPage === 'function') {
                    var pageIndex = window.viewer.currentPage(); // 0-based
                    pageNumber = pageIndex + 1; // Convert to 1-based
                }
                
                // Insert the page number tag
                if (pageNumber !== null) {
                    editor.insertText('<<' + pageNumber + '>>');
                } else {
                    // Fallback: ask user for page number
                    var userInput = prompt(local_lang.label.replace('<<', '').replace('>>', ''), '1');
                    if (userInput !== null && userInput.trim() !== '') {
                        editor.insertText('<<' + userInput.trim() + '>>');
                    }
                }
            }
        });

        editor.ui.addButton('Pagenumber', {
            label: local_lang.label,
            command: 'insertPageNumber',
            icon: this.path + 'images/pagenumber.gif'
        });
    }
});