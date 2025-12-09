/*
Copyright (c) 2025 Xavier Beheydt <xavier.beheydt@gmail.com>
*/

CKEDITOR.plugins.add('pagenumber', {
    init: function (editor) {
        var ckeditor_instance_id = '';
        var cur_lang = editor.config.language || CKEDITOR.lang.detect(CKEDITOR.config.defaultLanguage);
        var pagenumber_strings = {
            en: {
                label: "<<Page Number>>",
                dialog_title: 'Page Number',
                dialog_page_text: 'Page Number',
                dialog_page_text_empty_error: "Page number cannot be empty",
            },
            fr: {
                label: "<<Numéro Page>>",
                dialog_title: 'Numéro de page',
                dialog_page_text: 'Numéro de page',
                dialog_page_text_empty_error: "Le numéro de page ne peut pas être vide",
            }
        };
        var local_lang = pagenumber_strings[cur_lang] || pagenumber_strings['en'];

        editor.addCommand('pagenumberDialog', new CKEDITOR.dialogCommand('pagenumberDialog'));

        editor.ui.addButton('Pagenumber', {
            label: local_lang.label,
            command: 'pagenumberDialog',
            className: "x-cke_label_button"
        });

        CKEDITOR.dialog.add('pagenumberDialog', function(editor){
            return {
                title: local_lang.dialog_title,
                minWidth: 400,
                minHeight: 100,
                contents: [{
                    id: 'tab1',
                    label: local_lang.dialog_title,
                    elements: [{
                        type: 'text',
                        id: 'page-number',
                        label: local_lang.dialog_page_text,
                        validate: CKEDITOR.dialog.validate.notEmpty(local_lang.dialog_page_text_empty_error),
                        setup: function(element){
                            // no setup needed
                        },
                        commit: function(element){
                            // no commit needed here
                        }
                    }]
                }],
                onShow: function(){
                    // no element to setup
                },
                onOk: function(){
                    var page_number = this.getValueOf('tab1', 'page-number');
                    editor.insertText('<<' + page_number + '>>');
                }
            };
        });
    }
});