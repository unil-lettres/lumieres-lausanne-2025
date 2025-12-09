/*
Copyright (C) 2010-2025 Université de Lausanne, RISET
<https://www.unil.ch/riset/>

This file is part of Lumières.Lausanne.
Lumières.Lausanne is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Lumières.Lausanne is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

This copyright notice MUST APPEAR in all copies of the file.
*/

/**
 * Dialog definition for the Page Number plugin
 */

CKEDITOR.dialog.add('pagenumberDialog', function(editor) {
    var lang = editor.lang.pagenumber;
    
    return {
        title: lang.dialogTitle,
        minWidth: 350,
        minHeight: 120,
        
        contents: [
            {
                id: 'tab-basic',
                label: lang.dialogTitle,
                elements: [
                    {
                        type: 'text',
                        id: 'pageNumber',
                        label: lang.pageNumberLabel,
                        validate: function() {
                            var value = this.getValue();
                            if (!value || value.trim() === '') {
                                alert(lang.pageNumberEmpty);
                                return false;
                            }
                            if (!/^\d+$/.test(value.trim())) {
                                alert(lang.pageNumberInvalid);
                                return false;
                            }
                            return true;
                        },
                        setup: function(element) {
                            // Not used for creation
                        },
                        commit: function(data) {
                            data.pageNumber = this.getValue().trim();
                        }
                    }
                ]
            }
        ],
        
        onOk: function() {
            var data = {};
            this.commitContent(data);
            
            // Insert the page tag at cursor position
            var pageTag = '<<' + data.pageNumber + '>>';
            editor.insertHtml(pageTag);
        }
    };
});
