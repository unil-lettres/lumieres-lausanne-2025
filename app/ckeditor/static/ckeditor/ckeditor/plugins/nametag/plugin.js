/* Named-entity tagging — v0.1 (slice A)
 *
 * Adds the « Pers » and « Lieu » toolbar buttons to the transcription editor.
 * Each wraps the current selection in an inline tagged link pointing at a
 * biography (Person) or place (PlaceRecord) fiche:
 *
 *   <a class="ll-tag ll-tag-person" href="/fiches/bio/123/"  data-person="123" title="…">…</a>
 *   <a class="ll-tag ll-tag-place"  href="/fiches/lieu/15/"  data-place="15"   title="…">…</a>
 *
 * Slice A wires the buttons, the wrap/edit/remove lifecycle and a minimal
 * dialog (fiche id + label). The AJAX search window replaces the plain id
 * field in slice B.
 */

(function () {
    var KINDS = {
        person: {
            cssClass: 'll-tag-person',
            dataAttr: 'data-person',
            hrefBase: '/fiches/bio/',
            button: 'TagPerson',
            command: 'nametagPersonDialog',
            dialog: 'nametagPersonDialog',
            removeCommand: 'nametagPersonRemove',
            buttonLabel: 'Pers',
            buttonTitle: 'Lier une personne (biographie)',
            icon: 'icons/person.png',
            dialogTitle: 'Lier une personne',
            idLabel: 'Identifiant de la biographie'
        },
        place: {
            cssClass: 'll-tag-place',
            dataAttr: 'data-place',
            hrefBase: '/fiches/lieu/',
            button: 'TagPlace',
            command: 'nametagPlaceDialog',
            dialog: 'nametagPlaceDialog',
            removeCommand: 'nametagPlaceRemove',
            buttonLabel: 'Lieu',
            buttonTitle: 'Lier un lieu',
            icon: 'icons/place.png',
            dialogTitle: 'Lier un lieu',
            idLabel: 'Identifiant du lieu'
        }
    };

    // Walk up the ancestors and return the enclosing tag link, if any.
    function getContainer(conf, element) {
        var ancestors = element ? element.getParents(true) : [];
        for (var i = 0; i < ancestors.length; i++) {
            var el = ancestors[i];
            if (el.type === CKEDITOR.NODE_ELEMENT && el.getName() === 'a' && el.hasClass(conf.cssClass)) {
                return el;
            }
        }
        return null;
    }

    // Wrap the current selection in a fresh tagged link.
    function applyTag(editor, conf, id, label) {
        var attributes = {
            'class': 'll-tag ' + conf.cssClass,
            'href': conf.hrefBase + id + '/',
            'title': label || ''
        };
        attributes[conf.dataAttr] = String(id);
        new CKEDITOR.style({ element: 'a', attributes: attributes }).apply(editor.document);
    }

    // Refresh an existing tagged link in place.
    function updateTag(element, conf, id, label) {
        element.setAttribute('href', conf.hrefBase + id + '/');
        element.setAttribute(conf.dataAttr, String(id));
        element.setAttribute('title', label || '');
    }

    function makeDialog(conf) {
        return function (editor) {
            return {
                title: conf.dialogTitle,
                minWidth: 450,
                minHeight: 140,
                contents: [{
                    id: 'tab1',
                    label: conf.dialogTitle,
                    elements: [
                        {
                            type: 'text',
                            id: 'fiche_id',
                            label: conf.idLabel,
                            validate: CKEDITOR.dialog.validate.notEmpty('Indiquez l’identifiant de la fiche.'),
                            setup: function (data) {
                                this.setValue(data ? data.id : '');
                            }
                        },
                        {
                            type: 'text',
                            id: 'fiche_label',
                            label: 'Libellé affiché au survol (title)',
                            setup: function (data) {
                                this.setValue(data ? data.label : '');
                            }
                        }
                    ]
                }],
                onShow: function () {
                    var element = getContainer(conf, editor.getSelection().getStartElement());
                    this.element = element;
                    this.insertMode = !element;
                    if (this.insertMode) {
                        this.setupContent({ id: '', label: editor.getSelection().getSelectedText() });
                    } else {
                        this.setupContent({
                            id: element.getAttribute(conf.dataAttr),
                            label: element.getAttribute('title')
                        });
                    }
                },
                onOk: function () {
                    var id = CKEDITOR.tools.trim(this.getContentElement('tab1', 'fiche_id').getValue());
                    var label = this.getContentElement('tab1', 'fiche_label').getValue();
                    if (!id) {
                        return;
                    }
                    if (this.insertMode) {
                        applyTag(editor, conf, id, label);
                    } else {
                        updateTag(this.element, conf, id, label);
                    }
                }
            };
        };
    }

    function registerKind(editor, conf, pluginPath) {
        editor.addCommand(conf.command, new CKEDITOR.dialogCommand(conf.dialog));

        editor.addCommand(conf.removeCommand, {
            exec: function (ed) {
                var container = getContainer(conf, ed.getSelection().getStartElement());
                if (container) {
                    container.remove(true); // keep the inner text, drop the link
                }
            }
        });

        editor.ui.addButton(conf.button, {
            label: conf.buttonTitle,
            title: conf.buttonTitle,
            command: conf.command,
            icon: pluginPath + conf.icon
        });

        CKEDITOR.dialog.add(conf.dialog, makeDialog(conf));

        if (editor.contextMenu) {
            var editItem = conf.button + 'EditItem';
            var removeItem = conf.button + 'RemoveItem';
            editor.addMenuGroup('nametagGroup');
            editor.addMenuItem(editItem, {
                label: 'Modifier le lien ' + conf.buttonLabel,
                command: conf.command,
                group: 'nametagGroup'
            });
            editor.addMenuItem(removeItem, {
                label: 'Retirer le lien ' + conf.buttonLabel,
                command: conf.removeCommand,
                group: 'nametagGroup'
            });
            editor.contextMenu.addListener(function (element) {
                var container = getContainer(conf, element);
                if (container && !container.isReadOnly()) {
                    var menu = {};
                    menu[editItem] = CKEDITOR.TRISTATE_OFF;
                    menu[removeItem] = CKEDITOR.TRISTATE_OFF;
                    return menu;
                }
                return null;
            });
        }
    }

    CKEDITOR.plugins.add('nametag', {
        // NB: this CKEditor build expects `requires` to be an array and does not
        // split a string, so a `requires: 'dialog'` would be walked character by
        // character (loading bogus plugins d/i/a/l/o/g). The dialog plugin is
        // already loaded by the correction/notes buttons, so we declare nothing.
        init: function (editor) {
            var pluginPath = this.path;
            for (var kind in KINDS) {
                if (KINDS.hasOwnProperty(kind)) {
                    registerKind(editor, KINDS[kind], pluginPath);
                }
            }
        }
    });
})();
