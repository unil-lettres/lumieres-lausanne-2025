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
 * Page Number Plugin for CKEditor
 * This plugin adds a button to insert custom page tags in the format <<page_number>>
 */

CKEDITOR.plugins.add('pagenumber', {
    requires: 'dialog',
    lang: ['en', 'fr'],
    
    init: function(editor) {
        var pluginName = 'pagenumber';
        
        // Add the dialog command
        editor.addCommand('pagenumberDialog', new CKEDITOR.dialogCommand('pagenumberDialog'));
        
        // Add the toolbar button
        editor.ui.addButton('PageNumber', {
            label: editor.lang.pagenumber.label,
            command: 'pagenumberDialog',
            toolbar: 'insert',
            icon: this.path + 'pagenumber.png'
        });
        
        // Register the dialog
        CKEDITOR.dialog.add('pagenumberDialog', this.path + 'dialogs/pagenumber.js');
    }
});
