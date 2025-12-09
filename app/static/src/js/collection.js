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
 * Collection Management Module
 * Handles collection CRUD operations with modal dialogs
 */

import { $1, on, ajax } from './utils/dom.js';

class Collection {
  constructor() {
    this.currentId = null;
    this.urls = {
      create: '',
      edit: '',
      remove: '',
      popup: '',
    };
  }

  /**
   * Initialize collection module with URLs
   * @param {Object} urls - URL configuration
   */
  init(urls) {
    if (urls) {
      Object.assign(this.urls, urls);
    }
  }

  /**
   * Create modal dialog
   * @param {string} title - Dialog title
   * @param {string} content - Dialog HTML content
   * @param {Object} options - Dialog options
   * @returns {HTMLElement} Dialog element
   */
  createDialog(title, content, options = {}) {
    const dialog = document.createElement('div');
    dialog.className = 'modal-dialog';
    dialog.id = options.id || 'collection-dialog';

    dialog.innerHTML = `
      <div class="modal-overlay"></div>
      <div class="modal-content" style="width: ${options.width || 600}px;">
        <div class="modal-header">
          <h3>${title}</h3>
          <button class="modal-close" aria-label="Close">&times;</button>
        </div>
        <div class="modal-body">
          ${content}
        </div>
      </div>
    `;

    document.body.appendChild(dialog);

    // Close on overlay or close button click
    const overlay = $1('.modal-overlay', dialog);
    const closeBtn = $1('.modal-close', dialog);

    const closeDialog = () => {
      dialog.remove();
      if (options.onClose) {
        options.onClose();
      }
    };

    on(overlay, 'click', closeDialog);
    on(closeBtn, 'click', closeDialog);

    // ESC key to close
    const escapeHandler = (e) => {
      if (e.key === 'Escape') {
        closeDialog();
        document.removeEventListener('keydown', escapeHandler);
      }
    };
    document.addEventListener('keydown', escapeHandler);

    dialog.classList.add('active');

    return dialog;
  }

  /**
   * Create new collection
   * @param {Object} options - Options including callback
   */
  create(options = {}) {
    let url = this.urls.create;

    if (options.callback) {
      url += `?callback=${options.callback}`;
    }

    const content = `<iframe src="${url}" width="570" height="380" frameborder="0"></iframe>`;

    this.createDialog('Nouvelle collection', content, {
      id: 'collection-edit-dlog',
      width: 600,
      onClose: options.onClose,
    });
  }

  /**
   * Edit existing collection
   * @param {number} collId - Collection ID
   * @param {Object} options - Options including callback
   */
  edit(collId, options = {}) {
    if (!collId || isNaN(collId)) {
      return false;
    }

    let url = this.urls.edit.replace('__COLL_ID__', collId);

    if (options.callback) {
      url += (url.indexOf('?') > -1 ? '&' : '?') + `callback=${options.callback}`;
    }

    const content = `<iframe src="${url}" width="570" height="380" frameborder="0"></iframe>`;

    this.createDialog('Modification de la collection', content, {
      id: 'collection-edit-dlog',
      width: 600,
      onClose: options.onClose,
    });
  }

  /**
   * Close edit dialog
   */
  editClose() {
    const dialog = $1('#collection-edit-dlog');
    if (dialog) {
      dialog.remove();
    }
  }

  /**
   * Complete editing and optionally reload page
   * @param {Object} options - Options including no_reload flag
   */
  editDone(options = {}) {
    this.editClose();

    if (!options.no_reload) {
      window.location.reload();
    }

    return false;
  }

  /**
   * Remove collection with confirmation
   * @param {number} collId - Collection ID
   * @param {string} collTitle - Collection title
   */
  remove(collId, collTitle) {
    if (!collId || isNaN(collId)) {
      return false;
    }

    const content = `
      <p>Êtes-vous sûr de vouloir supprimer la collection &laquo;${collTitle}&raquo; ?</p>
      <div class="modal-actions">
        <button class="btn btn-danger" data-action="confirm">Supprimer</button>
        <button class="btn btn-secondary" data-action="cancel">Annuler</button>
      </div>
    `;

    const dialog = this.createDialog('Supprimer la collection', content, {
      width: 500,
    });

    // Handle button clicks
    on($1('[data-action="confirm"]', dialog), 'click', () => {
      const url = this.urls.remove.replace('__COLL_ID__', collId);

      ajax(url, { method: 'POST' })
        .then(() => {
          dialog.remove();
          window.location.reload();
        })
        .catch((error) => {
          console.error('Error removing collection:', error);
          alert('Erreur lors de la suppression de la collection');
        });
    });

    on($1('[data-action="cancel"]', dialog), 'click', () => {
      dialog.remove();
    });
  }

  /**
   * Display collection popup
   * @param {number} collId - Collection ID
   * @param {Object} options - Options
   */
  displayPopup(collId, options = {}) {
    if (!collId || isNaN(collId)) {
      return false;
    }

    const url = this.urls.popup.replace('__COLL_ID__', collId);
    const content = `<iframe src="${url}" width="100%" height="500" frameborder="0"></iframe>`;

    this.createDialog('Collection', content, {
      width: options.width || 800,
      onClose: options.onClose,
    });
  }
}

// Initialize and export
const collection = new Collection();

// Export for global use
window.collection = collection;

export default collection;
