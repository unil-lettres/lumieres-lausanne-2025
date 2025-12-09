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
 * Search Filter Module
 * Manages search filters for biographical searches
 */

import { $, $1, on, html, val, attr, data, closest, cookie } from './utils/dom.js';

class SearchFilter {
  constructor() {
    this.debug = true;
    this.filterDefinitions = null;
    this.filterApplied = null;
    this.filterImplied = null;
    this.filterElem = null;
    this.hooks = {};
    this.modelName = window.search_model_name || '';
  }

  /**
   * Initialize search filter system
   */
  init() {
    this.filterDefinitions = $1('#search-filter-definitions');
    this.filterApplied = $1('#search-filter-applied');
    this.filterImplied = $1('#search-filter-implied');

    if (!this.filterDefinitions || !this.filterApplied) {
      return;
    }

    this.filterElem = $1('.search-filter', this.filterDefinitions);

    // Bind events
    this.bindEvents();

    // Try to restore filters from cookie
    const savedFilters = cookie.get('fiches_search_filters');
    if (savedFilters) {
      this.unserializeFilters(savedFilters);
    } else {
      // Add initial empty filter
      this.filterAdd();
    }
  }

  /**
   * Bind event handlers
   */
  bindEvents() {
    // Add filter button
    on('.filter-add-btn', 'click', () => this.filterAdd());

    // Remove all filters button
    on('.filters-remove-all', 'click', () => this.filtersRemoveAll());

    // Delegate events to filter applied container
    on(this.filterApplied, 'click', (e) => {
      const target = e.target;

      if (target.classList.contains('filter-del')) {
        e.preventDefault();
        this.filterDel(target);
      } else if (target.classList.contains('filter-up')) {
        e.preventDefault();
        this.filterMove(target, 'up');
      } else if (target.classList.contains('filter-down')) {
        e.preventDefault();
        this.filterMove(target, 'down');
      }
    });

    // Filter class change
    on(this.filterApplied, 'change', (e) => {
      if (e.target.name === 'filter_class') {
        this.filterClassChange(e.target);
      } else if (e.target.name === 'op') {
        this.filterOperatorChange(e.target);
      }
    });
  }

  /**
   * Add a new filter
   */
  filterAdd() {
    if (!this.filterElem) {
      return null;
    }

    const newFilter = this.filterElem.cloneNode(true);
    this.filterApplied.appendChild(newFilter);
    this.updateFilterDisplay();

    // Call post hook if exists
    if (this.hooks.post_filter_add) {
      this.hooks.post_filter_add(newFilter);
    }

    return newFilter;
  }

  /**
   * Delete a filter
   * @param {Element} element - Element within the filter to delete
   */
  filterDel(element) {
    const filter = closest(element, '.search-filter');
    if (filter && filter.parentNode) {
      filter.parentNode.removeChild(filter);
      this.updateFilterDisplay();
    }
  }

  /**
   * Remove all filters
   */
  filtersRemoveAll() {
    const filters = $('.search-filter', this.filterApplied);
    filters.forEach((filter) => filter.parentNode.removeChild(filter));

    cookie.delete('fiches_search_filters');
    this.filterAdd();
  }

  /**
   * Move filter up or down
   * @param {Element} element - Element within the filter to move
   * @param {string} dir - Direction: 'up' or 'down'
   */
  filterMove(element, dir) {
    const filter = closest(element, '.search-filter');
    if (!filter) {
      return;
    }

    if (dir === 'up' && filter.previousElementSibling) {
      filter.parentNode.insertBefore(filter, filter.previousElementSibling);
    } else if (dir === 'down' && filter.nextElementSibling) {
      filter.parentNode.insertBefore(filter.nextElementSibling, filter);
    }

    this.updateFilterDisplay();
  }

  /**
   * Update filter display states (show/hide buttons)
   */
  updateFilterDisplay() {
    const filters = $('.search-filter', this.filterApplied);
    const filterCount = filters.length;

    filters.forEach((filter, index) => {
      const opBtn = $1('.filter-op', filter);
      const delBtn = $1('.filter-del', filter);
      const upBtn = $1('.filter-up', filter);
      const downBtn = $1('.filter-down', filter);

      // Reset visibility
      [opBtn, delBtn, upBtn, downBtn].forEach((btn) => {
        if (btn) {
          btn.style.visibility = 'visible';
        }
      });

      // First filter: hide op and up
      if (index === 0) {
        if (opBtn) opBtn.style.visibility = 'hidden';
        if (upBtn) upBtn.style.visibility = 'hidden';
      }

      // Last filter: hide down
      if (index === filterCount - 1) {
        if (downBtn) downBtn.style.visibility = 'hidden';
      }

      // Single filter: hide delete
      if (filterCount === 1) {
        if (delBtn) delBtn.style.visibility = 'hidden';
      }
    });
  }

  /**
   * Handle filter class change
   * @param {Element} classSelector - The select element that changed
   */
  filterClassChange(classSelector) {
    const filterClass = val(classSelector);
    const sourceFilter = $1(`.filter-${filterClass}`, this.filterDefinitions);

    if (!sourceFilter) {
      return;
    }

    const filterContent = sourceFilter.cloneNode(true);
    const filter = closest(classSelector, '.search-filter');
    const placeholder = $1('.filter-content-placeholder', filter);

    if (placeholder) {
      html(placeholder, '');
      placeholder.appendChild(filterContent);
    }

    // Call post hook if exists
    if (this.hooks.post_filter_class_change) {
      this.hooks.post_filter_class_change(filterContent);
    }
  }

  /**
   * Handle filter operator change
   * @param {Element} operatorSelect - The operator select element
   */
  filterOperatorChange(operatorSelect) {
    const operator = val(operatorSelect);
    const filterContent = closest(operatorSelect, '.search-filter-content');

    if (!filterContent) {
      return;
    }

    // Hide all operator-specific fields
    const opSpecs = $('.op_spec', filterContent);
    opSpecs.forEach((spec) => {
      spec.style.display = 'none';
    });

    // Show relevant operator field
    const relevantOp = $1(`.op_${operator}`, filterContent);
    if (relevantOp) {
      relevantOp.style.display = '';
    }

    // Focus next input
    if (operatorSelect.nextElementSibling) {
      operatorSelect.nextElementSibling.focus();
    }
  }

  /**
   * Get filters query object
   * @returns {Object} Query object with model name and filters
   */
  getFiltersQuery() {
    const filtersDef = [];
    const containers = [this.filterApplied, this.filterImplied].filter(Boolean);

    containers.forEach((container) => {
      const filterContents = $('.search-filter-content', container);

      filterContents.forEach((content) => {
        const filter = closest(content, '.search-filter');
        const parts = [];

        const filterOp = val($1('[name=filter_op]', filter)) || 'and';
        const filterClass = val($1('[name=filter_class]', filter));

        // Run pre-process hooks
        const preHooks = $('[name=pre-process-hook]', content);
        preHooks.forEach((hook) => {
          const hookName = val(hook);
          if (this.hooks[hookName]) {
            this.hooks[hookName](content);
          }
        });

        // Process each filter part
        const contentParts = $('.search-filter-content-part', content);
        contentParts.forEach((part) => {
          const filterObj = {
            attr: val($1('[name=attr]', part)),
            type: val($1('[name=type]', part)),
            op: val($1('[name=op]', part)),
            val: val($1('[name=val]', part)),
          };

          if (typeof filterObj.val === 'undefined') {
            return;
          }

          // Handle range operator
          if (filterObj.op === 'range') {
            const val1 = val($1('[name=val1]', part));
            this.handleRangeFilter(filterObj, val1, parts);
            return;
          }

          // Handle number validation
          if (filterObj.type === 'number' && filterObj.val === 'notnull') {
            if (isNaN(parseInt(filterObj.val))) {
              filterObj.op = 'isnull';
              filterObj.val = '0';
            }
          }

          // Handle string validation
          if (filterObj.type === 'string' && filterObj.val === 'notnull') {
            filterObj.op = 'isnull';
            filterObj.val = '';
          }

          if (filterObj.val !== '') {
            parts.push(filterObj);
          }
        });

        // Run post-process hooks
        const postHooks = $('[name=post-process-hook]', content);
        postHooks.forEach((hook) => {
          const hookName = val(hook);
          if (this.hooks[hookName]) {
            this.hooks[hookName](content, {
              op: filterOp,
              cl: filterClass,
              params: parts,
            });
          }
        });

        if (parts.length > 0) {
          filtersDef.push({ op: filterOp, cl: filterClass, params: parts });
        }
      });
    });

    return { model_name: this.modelName, filters: filtersDef };
  }

  /**
   * Handle range filter logic
   * @param {Object} filterObj - Filter object
   * @param {string} val1 - Second value for range
   * @param {Array} parts - Parts array to push to
   */
  handleRangeFilter(filterObj, val1, parts) {
    let cVal = parseInt(filterObj.val);
    let cVal1 = parseInt(val1);

    if (isNaN(cVal)) {
      if (isNaN(cVal1)) {
        // Both invalid, abort
        return;
      }
      // No valid start, make it "before" query
      filterObj.op = 'lt';
      filterObj.val = cVal1;
      parts.push(filterObj);
      return;
    }

    if (isNaN(cVal1)) {
      // No valid end, make it "after" query
      filterObj.op = 'gt';
      filterObj.val = cVal;
      parts.push(filterObj);
      return;
    }

    // Valid range: ensure correct order
    if (cVal1 < cVal) {
      [cVal, cVal1] = [cVal1, cVal];
    }

    // Save original operator
    filterObj.op_origin = 'range';

    // Add both range limits
    parts.push({ ...filterObj, val: cVal, op: 'gt' });
    parts.push({ ...filterObj, val: cVal1, op: 'lt' });
  }

  /**
   * Serialize filters to JSON string
   * @returns {string} JSON string
   */
  serializeFilters() {
    return JSON.stringify(this.getFiltersQuery());
  }

  /**
   * Unserialize filters from JSON string
   * @param {string} jsonStr - JSON string
   * @returns {boolean} Success status
   */
  unserializeFilters(jsonStr) {
    try {
      const filtersDef = JSON.parse(jsonStr);

      if (filtersDef.model_name !== this.modelName) {
        return false;
      }

      filtersDef.filters.forEach((fDef) => {
        // Skip if already in implied filters
        if ($1(`.filter-${fDef.cl}`, this.filterImplied)) {
          return;
        }

        const newFilter = this.filterAdd();
        if (!newFilter) {
          return;
        }

        // Set filter operator
        const opSelect = $1('[name=filter_op]', newFilter);
        if (opSelect) {
          val(opSelect, fDef.op);
        }

        // Set filter class and trigger change
        const classSelect = $1('.filter-class', newFilter);
        if (classSelect) {
          val(classSelect, fDef.cl);
          classSelect.dispatchEvent(new Event('change', { bubbles: true }));
        }

        // Set parameters
        const parts = $('.search-filter-content-part', newFilter);
        let pIdx = 0;

        fDef.params.forEach((param, index) => {
          if (index < parts.length) {
            const part = parts[index];
            const op = param.op_origin || param.op;

            const attrInput = $1('[name=attr]', part);
            const opSelect = $1('[name=op]', part);
            const typeInput = $1('[name=type]', part);
            const valInput = $1('[name=val]', part);

            if (attrInput) val(attrInput, param.attr);
            if (opSelect) {
              val(opSelect, op);
              opSelect.dispatchEvent(new Event('change', { bubbles: true }));
            }
            if (typeInput) val(typeInput, param.type);
            if (valInput) val(valInput, param.val);

            // Handle range operator
            if (op === 'range' && fDef.params[index + 1]) {
              const val1Input = $1('[name=val1]', part);
              if (val1Input) {
                val(val1Input, fDef.params[index + 1].val);
              }
            }
          }
        });

        // Call post hook if exists
        if (this.hooks.post_unserialize_filter) {
          this.hooks.post_unserialize_filter(fDef, newFilter);
        }
      });

      return true;
    } catch (e) {
      console.error('Error unserializing filters:', e);
      return false;
    }
  }
}

// Initialize and export
const searchFilter = new SearchFilter();

// Export for global use
window.search_filter = searchFilter;

export default searchFilter;
