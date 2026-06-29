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
      searchLabel: 'Rechercher une personne',
      statusId: 'nametag-status-person',
      searchUrl: '/fiches/ajax_search/',
      searchParams: 'app_label=fiches&model_name=Person&search_field=name&outf=_m__format_for_ajax_search',
      // ajax_search ORs the words of `q`; AND the extra words via and_queries
      // so "Jean Barbeyrac" matches the person whose name holds both terms.
      andSearchField: 'name',
      // Inline creation (Directeurs only — gated server-side too).
      permKey: 'person',
      createUrl: '/fiches/tagging/person/create/',
      createStatusId: 'nametag-create-status-person',
      needsCategory: false
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
      searchLabel: 'Rechercher un lieu',
      statusId: 'nametag-status-place',
      searchUrl: '/fiches/lieu/autocomplete/',
      searchParams: '',
      // Inline creation (Directeurs only — gated server-side too).
      permKey: 'place',
      createUrl: '/fiches/tagging/place/create/',
      categoriesUrl: '/fiches/tagging/place/categories/',
      createStatusId: 'nametag-create-status-place',
      needsCategory: true
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

  // Robustly find the tag link for the current selection, whether the caret sits
  // inside it, the link itself is selected, or the selection starts within it.
  // This is what lets "edit" update a tag in place instead of nesting a new one.
  function findTag(conf, selection) {
    if (!selection) {
      return null;
    }
    var candidates = [];
    if (selection.getSelectedElement) {
      candidates.push(selection.getSelectedElement());
    }
    candidates.push(selection.getStartElement());
    var ranges = selection.getRanges();
    if (ranges && ranges.length) {
      var node = ranges[0].startContainer;
      if (node) {
        candidates.push(node.type === CKEDITOR.NODE_ELEMENT ? node : node.getParent());
      }
    }
    for (var i = 0; i < candidates.length; i++) {
      var found = getContainer(conf, candidates[i]);
      if (found) {
        return found;
      }
    }
    return null;
  }

  // Return the enclosing editorial-correction span (<span class="sic" data-corr>)
  // of a node, if any, so a tag can swallow the whole correction instead of
  // splitting it — the corrected word must stay clickable in both renderings.
  function correctionAncestor(node) {
    if (!node) {
      return null;
    }
    var parents = node.getParents(true);
    for (var i = 0; i < parents.length; i++) {
      var p = parents[i];
      if (p.type === CKEDITOR.NODE_ELEMENT && p.getName() === 'span' && p.hasClass('sic')) {
        return p;
      }
    }
    return null;
  }

  // Grow a range so neither boundary cuts through an editorial correction:
  // tagging a corrected word must keep its <span class="sic"> intact.
  function expandRangeOverCorrections(range) {
    var startSic = correctionAncestor(range.startContainer);
    if (startSic) {
      range.setStartBefore(startSic);
    }
    var endSic = correctionAncestor(range.endContainer);
    if (endSic) {
      range.setEndAfter(endSic);
    }
  }

  // Give every editorial correction inside a node back its diplomatic tooltip
  // (kept in data-corr), so the sic popup reappears once it leaves a tag.
  function restoreCorrectionTitles(node) {
    var spans = node.getElementsByTag('span');
    for (var i = 0; i < spans.count(); i++) {
      var span = spans.getItem(i);
      if (span.hasClass('sic')) {
        var corr = span.getAttribute('data-corr');
        if (corr && !span.getAttribute('title')) {
          span.setAttribute('title', corr);
        }
      }
    }
  }

  // Hide the diplomatic tooltip of every correction now inside a tag, so
  // hovering shows the person/place tooltip; the reading survives in data-corr.
  function hideCorrectionTitles(node) {
    var spans = node.getElementsByTag('span');
    for (var i = 0; i < spans.count(); i++) {
      var span = spans.getItem(i);
      if ((span.hasClass('sic') || span.hasClass('corr')) && span.getAttribute('title')) {
        span.removeAttribute('title');
      }
    }
  }

  // Same-kind tags whose bounds the selection straddles (an ancestor of either
  // boundary). Used to preselect the fiche when a selection re-bounds a tag.
  function overlappingTags(conf, selection) {
    var ranges = selection ? selection.getRanges() : [];
    if (!ranges.length) {
      return [];
    }
    var range = ranges[0];
    var tags = [];
    function climb(node) {
      if (!node) {
        return;
      }
      var parents = node.getParents(true);
      for (var i = 0; i < parents.length; i++) {
        var el = parents[i];
        if (el.type === CKEDITOR.NODE_ELEMENT && el.getName() === 'a' && el.hasClass(conf.cssClass)) {
          var seen = false;
          for (var k = 0; k < tags.length; k++) {
            if (tags[k].equals(el)) {
              seen = true;
              break;
            }
          }
          if (!seen) {
            tags.push(el);
          }
        }
      }
    }
    climb(range.startContainer);
    climb(range.endContainer);
    return tags;
  }

  // Unwrap any same-kind tag that is an ancestor of the given bookmark marker,
  // i.e. a tag the new selection only partially covers. Unwrapping frees the
  // whole tag — including the part outside the selection — to plain text, which
  // is what shrinking a tag to a sub-selection requires. Correction tooltips are
  // restored; the ones that end up back inside the new tag are hidden afterwards.
  function absorbAncestorTags(conf, marker) {
    if (!marker) {
      return;
    }
    var parents = marker.getParents(true);
    for (var i = 0; i < parents.length; i++) {
      var el = parents[i];
      if (el.type === CKEDITOR.NODE_ELEMENT && el.getName() === 'a' && el.hasClass(conf.cssClass)) {
        restoreCorrectionTitles(el);
        el.remove(true);
      }
    }
  }

  // Unwrap any same-kind tag fully enclosed in a node (a tag the selection
  // swallowed whole), merging its text into the node.
  function unwrapEnclosedTags(conf, node) {
    var links = node.getElementsByTag('a');
    var hits = [];
    for (var i = 0; i < links.count(); i++) {
      var a = links.getItem(i);
      if (a.hasClass(conf.cssClass)) {
        hits.push(a);
      }
    }
    for (var j = 0; j < hits.length; j++) {
      hits[j].remove(true);
    }
  }

  // Build a fresh tagged <a> (without inserting it). Mirrors updateTag so the
  // href shadow stays consistent (see issue #122). Links are built by hand (like
  // the native link plugin) because CKEditor's style system treats <a> specially.
  function newTagElement(editor, conf, id, label) {
    var href = conf.hrefBase + id + '/';
    var link = editor.document.createElement('a');
    link.setAttributes({
      'class': 'll-tag ' + conf.cssClass,
      'href': href,
      'data-cke-saved-href': href,
      'title': label || ''
    });
    link.setAttribute(conf.dataAttr, String(id));
    return link;
  }

  // Apply a tag to the current selection, normalising the result to a single
  // link that spans exactly the selection. Any same-kind tag the selection
  // touches is absorbed: enclosed ones are merged in, partially-covered ones are
  // freed (their outside part becomes plain text again). Editorial corrections
  // inside the new tag get their diplomatic tooltip hidden. With no selection,
  // the label text is dropped in as a fresh tag.
  function applyTag(editor, conf, id, label) {
    var selection = editor.getSelection();
    var ranges = selection ? selection.getRanges() : [];

    if (!ranges.length || ranges[0].collapsed) {
      // No selection: drop the label text as the link content.
      var bare = newTagElement(editor, conf, id, label);
      bare.setText(label || String(id));
      editor.insertElement(bare);
      return;
    }

    // Keep whole corrections inside the new bounds, then bookmark with real
    // markers so the boundaries survive the unwrapping that follows.
    var range = ranges[0];
    expandRangeOverCorrections(range);
    selection.selectRanges([range]);
    var bookmark = selection.createBookmarks(false);
    absorbAncestorTags(conf, bookmark[0].startNode);
    absorbAncestorTags(conf, bookmark[0].endNode);
    selection.selectBookmarks(bookmark);

    var wrapRange = selection.getRanges()[0];
    var link = newTagElement(editor, conf, id, label);
    link.append(wrapRange.extractContents());
    unwrapEnclosedTags(conf, link); // same-kind tags swallowed whole
    hideCorrectionTitles(link); // corrections now under the tag
    wrapRange.insertNode(link);
    selection.selectElement(link);
  }

  // Refresh an existing tagged link in place.
  function updateTag(element, conf, id, label) {
    var href = conf.hrefBase + id + '/';
    element.setAttribute('href', href);
    // CKEditor shadows href as data-cke-saved-href on load and, on output, the
    // html data processor drops the live href and re-emits the saved one. Update
    // both, otherwise the saved copy would resurrect the previous fiche's href
    // while data-* and title already point to the new one (issue #122).
    element.setAttribute('data-cke-saved-href', href);
    element.setAttribute(conf.dataAttr, String(id));
    element.setAttribute('title', label || '');
  }

  // Unwrap a tag link, keeping its inner text. When the link wrapped an editorial
  // correction, applyTag hid the <span class="sic"> title so the tooltip would
  // show the person/place rather than the correction; restore it from data-corr
  // here, otherwise the diplomatic tooltip stays gone once the link is removed
  // (the correction itself survives in data-corr regardless).
  function removeTag(container) {
    if (!container) {
      return;
    }
    restoreCorrectionTitles(container);
    container.remove(true); // unwrap: keep the inner text, drop the link
  }

  // Trim helper that does not rely on String.prototype.trim (old browsers).
  function trim(value) {
    return (value || '').replace(/^\s+|\s+$/g, '');
  }

  // Split a query into plain search words: drop bracketed dates "[1674-1744]",
  // parenthetical qualifiers "(canton)" and punctuation so a prefilled label
  // ("Barbeyrac, Jean [1674-1744]") becomes usable terms ("Barbeyrac", "Jean").
  function searchWords(query) {
    return trim(query)
      .replace(/\[[^\]]*\]/g, ' ')
      .replace(/\([^)]*\)/g, ' ')
      .replace(/[,.;:]/g, ' ')
      .split(/\s+/)
      .filter(function (word) {
        return word.length > 0;
      });
  }

  // Query a search endpoint; call back with [{label, id}] and the HTTP status.
  // Both endpoints answer with one "Label|id" line per match.
  function fetchResults(conf, query, callback) {
    var words = searchWords(query);
    if (!words.length) {
      callback([], 200);
      return;
    }
    var url = conf.searchUrl + '?' + (conf.searchParams ? conf.searchParams + '&' : '');
    if (conf.andSearchField) {
      // ajax_search ORs the words of `q`; keep the first as `q` and AND the
      // rest via and_queries so every term must match.
      url += 'q=' + encodeURIComponent(words[0]);
      if (words.length > 1) {
        var andQueries = [];
        for (var i = 1; i < words.length; i++) {
          andQueries.push({ field: conf.andSearchField, value: words[i] });
        }
        url += '&and_queries=' + encodeURIComponent(JSON.stringify(andQueries));
      }
    } else {
      url += 'q=' + encodeURIComponent(words.join(' '));
    }
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.onreadystatechange = function () {
      if (xhr.readyState !== 4) {
        return;
      }
      var items = [];
      if (xhr.status === 200) {
        xhr.responseText.split('\n').forEach(function (line) {
          line = trim(line);
          var sep = line.lastIndexOf('|');
          if (sep === -1) {
            return;
          }
          // Parenthesise the trailing birth-death dates that format_for_ajax_search
          // emits bracketed: "Nom, Prénom [1698-1756]" -> "Nom, Prénom (1698-1756)".
          var label = line.substring(0, sep).replace(/\s*\[(\d{0,4}-\d{0,4})\]\s*$/, ' ($1)');
          items.push({ label: label, id: line.substring(sep + 1) });
        });
      }
      callback(items, xhr.status);
    };
    xhr.send();
  }

  function setStatus(conf, message) {
    var node = CKEDITOR.document.getById(conf.statusId);
    if (node) {
      node.setHtml(message);
    }
  }

  // Refresh the results listbox; keepId/keepLabel preserve the currently linked
  // fiche when editing an existing tag, even if it is not in the search hits.
  function populateResults(dialog, conf, items, keepId, keepLabel) {
    var results = dialog.getContentElement('tab1', 'results');
    results.clear();
    dialog._nametagMap = {};
    items.forEach(function (item) {
      results.add(item.label, item.id);
      dialog._nametagMap[item.id] = item.label;
    });
    if (keepId && !dialog._nametagMap[keepId]) {
      results.add(keepLabel || ('#' + keepId), keepId);
      dialog._nametagMap[keepId] = keepLabel || ('#' + keepId);
    }
    if (keepId) {
      results.setValue(keepId);
    }
    setStatus(conf, items.length ? (items.length + ' résultat(s).') : 'Aucune fiche trouvée.');
  }

  function runSearch(dialog, conf, query, keepId, keepLabel) {
    query = trim(query);
    if (!query) {
      dialog.getContentElement('tab1', 'results').clear();
      dialog._nametagMap = {};
      setStatus(conf, 'Saisissez un terme de recherche.');
      return;
    }
    setStatus(conf, 'Recherche…');
    fetchResults(conf, query, function (items, status) {
      if (status !== 200) {
        setStatus(conf, 'Erreur de recherche (HTTP ' + status + ').');
        return;
      }
      populateResults(dialog, conf, items, keepId, keepLabel);
    });
  }

  // --- Inline fiche creation (Directeurs only) -----------------------------

  // Whether the current user may create this kind of fiche. The page sets the
  // server-side permissions on window.LL_NAMETAG; creation is gated again on
  // the server, so this only governs whether the UI is offered.
  function canCreate(conf) {
    return !!(window.LL_NAMETAG && window.LL_NAMETAG[conf.permKey]);
  }

  function getCookie(name) {
    var match = document.cookie.match(new RegExp('(^|;\\s*)' + name + '=([^;]*)'));
    return match ? decodeURIComponent(match[2]) : '';
  }

  function setCreateStatus(conf, message) {
    var node = CKEDITOR.document.getById(conf.createStatusId);
    if (node) {
      node.setHtml(message);
    }
  }

  // Add one fiche to the results listbox and select it.
  function selectResult(dialog, id, label) {
    var results = dialog.getContentElement('tab1', 'results');
    if (!dialog._nametagMap) {
      dialog._nametagMap = {};
    }
    if (!dialog._nametagMap[id]) {
      results.add(label, id);
      dialog._nametagMap[id] = label;
    }
    results.setValue(id);
  }

  var categoriesCache = null;

  function loadCategories(conf, selectEl) {
    function fill(list) {
      selectEl.clear();
      selectEl.add('— Catégorie —', '');
      list.forEach(function (category) {
        selectEl.add(category.name, String(category.id));
      });
    }
    if (categoriesCache) {
      fill(categoriesCache);
      return;
    }
    var xhr = new XMLHttpRequest();
    xhr.open('GET', conf.categoriesUrl, true);
    xhr.onreadystatechange = function () {
      if (xhr.readyState !== 4 || xhr.status !== 200) {
        return;
      }
      try {
        categoriesCache = JSON.parse(xhr.responseText).categories || [];
      } catch (e) {
        categoriesCache = [];
      }
      fill(categoriesCache);
    };
    xhr.send();
  }

  function createFiche(conf, dialog) {
    var name = trim(dialog.getContentElement('tab1', 'create_name').getValue());
    if (!name) {
      setCreateStatus(conf, 'Indiquez un nom.');
      return;
    }
    var payload = 'name=' + encodeURIComponent(name);
    if (conf.needsCategory) {
      var categoryId = dialog.getContentElement('tab1', 'create_category').getValue();
      if (!categoryId) {
        setCreateStatus(conf, 'Choisissez une catégorie.');
        return;
      }
      payload += '&category=' + encodeURIComponent(categoryId);
    }
    setCreateStatus(conf, 'Création…');
    var xhr = new XMLHttpRequest();
    xhr.open('POST', conf.createUrl, true);
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8');
    xhr.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    xhr.onreadystatechange = function () {
      if (xhr.readyState !== 4) {
        return;
      }
      var data = null;
      try {
        data = JSON.parse(xhr.responseText);
      } catch (e) {
        data = null;
      }
      if (xhr.status === 200 && data && data.success) {
        selectResult(dialog, String(data.id), data.label);
        setCreateStatus(conf, data.created ? 'Fiche créée et sélectionnée — validez par OK.' : 'Fiche existante sélectionnée.');
      } else if (xhr.status === 403) {
        setCreateStatus(conf, 'Vous n’avez pas le droit de créer cette fiche.');
      } else {
        setCreateStatus(conf, 'Échec de la création (HTTP ' + xhr.status + ').');
      }
    };
    xhr.send(payload);
  }

  function makeDialog(conf) {
    return function (editor) {
      return {
        title: conf.dialogTitle,
        minWidth: 480,
        minHeight: 340,
        contents: [{
          id: 'tab1',
          label: conf.dialogTitle,
          elements: [
            {
              type: 'text',
              id: 'search',
              label: conf.searchLabel
            },
            {
              type: 'select',
              id: 'results',
              label: 'Résultats',
              size: 8,
              items: [],
              style: 'width:100%;'
            },
            {
              type: 'html',
              html: '<div id="' + conf.statusId + '" class="nametag-status" ' +
                'style="color:#666;font-size:11px;margin-top:2px;"></div>'
            },
            {
              type: 'vbox',
              id: 'createBox',
              children: [
                {
                  type: 'html',
                  html: '<hr style="margin:8px 0 4px"><strong>Créer une nouvelle fiche</strong>'
                },
                { type: 'text', id: 'create_name', label: 'Nom' }
              ]
                .concat(
                  conf.needsCategory
                    ? [
                      {
                        type: 'select',
                        id: 'create_category',
                        label: 'Catégorie',
                        items: [],
                        style: 'width:100%;'
                      }
                    ]
                    : []
                )
                .concat([
                  {
                    type: 'button',
                    id: 'create_btn',
                    label: 'Créer la fiche',
                    onClick: function () {
                      createFiche(conf, this.getDialog());
                    }
                  },
                  {
                    type: 'html',
                    html:
                      '<div id="' +
                      conf.createStatusId +
                      '" style="color:#666;font-size:11px;margin-top:2px;"></div>'
                  }
                ])
            }
          ]
        }],
        // Wire the debounced search once, when the dialog DOM is first built.
        onLoad: function () {
          var dialog = this;
          var searchEl = dialog.getContentElement('tab1', 'search');
          var timer = null;
          searchEl.getInputElement().on('keyup', function () {
            if (timer) {
              clearTimeout(timer);
            }
            timer = setTimeout(function () {
              runSearch(dialog, conf, searchEl.getValue());
            }, 250);
          });
          dialog.getContentElement('tab1', 'results').getInputElement().on('dblclick', function () {
            var ok = dialog.getButton('ok');
            if (ok) {
              ok.click();
            }
          });
          if (conf.needsCategory) {
            loadCategories(conf, dialog.getContentElement('tab1', 'create_category'));
          }
        },
        onShow: function () {
          var dialog = this;
          var selection = editor.getSelection();
          var ranges = selection ? selection.getRanges() : [];
          var hasSelection = !!(ranges.length && !ranges[0].collapsed);
          var container = findTag(conf, selection);
          // Edit a tag in place only when the caret sits in it without a
          // selection; any selection (re)bounds a tag to the selected text.
          this.element = (!hasSelection && container) ? container : null;
          this.insertMode = !this.element;
          this._nametagMap = {};
          this._nametagBookmarks = null;
          this.getContentElement('tab1', 'results').clear();
          // The "remove" button only makes sense when editing a tag in place.
          var removeButton = this.getButton('nametagRemove');
          if (removeButton) {
            removeButton.getElement()[this.element ? 'show' : 'hide']();
          }
          // Offer inline creation only to users allowed to create.
          var createBox = this.getContentElement('tab1', 'createBox');
          if (createBox) {
            createBox.getElement()[canCreate(conf) ? 'show' : 'hide']();
          }
          setCreateStatus(conf, '');

          if (this.element) {
            // Edit in place: prefill with the tag's current fiche.
            this.getContentElement('tab1', 'create_name').setValue('');
            var curId = this.element.getAttribute(conf.dataAttr);
            var curLabel = this.element.getAttribute('title') || this.element.getText();
            this.getContentElement('tab1', 'search').setValue(curLabel);
            runSearch(dialog, conf, curLabel, curId, curLabel);
            return;
          }

          var selText = hasSelection ? trim(selection.getSelectedText()) : '';
          this.getContentElement('tab1', 'create_name').setValue(selText);
          if (!hasSelection) {
            // Caret in plain text, no tag: a fresh tag from the label text.
            this.getContentElement('tab1', 'search').setValue('');
            runSearch(dialog, conf, '');
            return;
          }
          // Remember the selection so the tag still wraps it after focus moves
          // to the dialog fields.
          this._nametagBookmarks = selection.createBookmarks(true);
          // If the selection re-bounds exactly one existing tag, keep that fiche
          // preselected so confirming just changes the bounds.
          var overlap = overlappingTags(conf, selection);
          if (overlap.length === 1) {
            var oid = overlap[0].getAttribute(conf.dataAttr);
            var olabel = overlap[0].getAttribute('title') || overlap[0].getText();
            this.getContentElement('tab1', 'search').setValue(olabel);
            runSearch(dialog, conf, olabel, oid, olabel);
          } else {
            this.getContentElement('tab1', 'search').setValue(selText);
            runSearch(dialog, conf, selText);
          }
        },
        onOk: function () {
          var id = this.getContentElement('tab1', 'results').getValue();
          if (!id) {
            setStatus(conf, 'Sélectionnez une fiche dans la liste.');
            return false;
          }
          var label = (this._nametagMap && this._nametagMap[id]) || '';
          if (this.insertMode) {
            if (this._nametagBookmarks) {
              editor.getSelection().selectBookmarks(this._nametagBookmarks);
              this._nametagBookmarks = null;
            }
            applyTag(editor, conf, id, label);
          } else {
            updateTag(this.element, conf, id, label);
          }
        },
        // Remove leftover bookmark markers if the user closes without tagging.
        onCancel: function () {
          if (this._nametagBookmarks) {
            editor.getSelection().selectBookmarks(this._nametagBookmarks);
            this._nametagBookmarks = null;
          }
        },
        buttons: [
          {
            type: 'button',
            id: 'nametagRemove',
            label: 'Retirer le lien',
            title: 'Retirer ce lien (garde le texte)',
            onClick: function () {
              var dialog = this.getDialog();
              if (dialog.element) {
                removeTag(dialog.element);
              }
              dialog.hide();
            }
          },
          CKEDITOR.dialog.cancelButton,
          CKEDITOR.dialog.okButton
        ]
      };
    };
  }

  function registerKind(editor, conf, pluginPath) {
    editor.addCommand(conf.command, new CKEDITOR.dialogCommand(conf.dialog));

    editor.addCommand(conf.removeCommand, {
      exec: function (ed) {
        removeTag(findTag(conf, ed.getSelection()));
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
