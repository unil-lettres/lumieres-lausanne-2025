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
 * DOM Utilities - Vanilla JS replacements for common jQuery operations
 */

/**
 * Query selector with multiple element support
 * @param {string} selector - CSS selector
 * @param {Element} context - Context element (default: document)
 * @returns {NodeList|Element|null}
 */
export function $(selector, context = document) {
  return context.querySelectorAll(selector);
}

/**
 * Query single element
 * @param {string} selector - CSS selector
 * @param {Element} context - Context element (default: document)
 * @returns {Element|null}
 */
export function $1(selector, context = document) {
  return context.querySelector(selector);
}

/**
 * Add event listener to element(s)
 * @param {Element|NodeList|string} target - Element, NodeList, or selector
 * @param {string} event - Event name
 * @param {Function} handler - Event handler
 * @param {Element} context - Context for selector
 */
export function on(target, event, handler, context = document) {
  const elements = typeof target === 'string' ? $(target, context) : target;
  const nodeList = elements instanceof Element ? [elements] : elements;

  nodeList.forEach((el) => {
    if (el) {
      el.addEventListener(event, handler);
    }
  });
}

/**
 * Remove event listener from element(s)
 * @param {Element|NodeList|string} target - Element, NodeList, or selector
 * @param {string} event - Event name
 * @param {Function} handler - Event handler
 * @param {Element} context - Context for selector
 */
export function off(target, event, handler, context = document) {
  const elements = typeof target === 'string' ? $(target, context) : target;
  const nodeList = elements instanceof Element ? [elements] : elements;

  nodeList.forEach((el) => {
    if (el) {
      el.removeEventListener(event, handler);
    }
  });
}

/**
 * Add class to element(s)
 * @param {Element|NodeList|string} target - Element, NodeList, or selector
 * @param {string} className - Class name to add
 * @param {Element} context - Context for selector
 */
export function addClass(target, className, context = document) {
  const elements = typeof target === 'string' ? $(target, context) : target;
  const nodeList = elements instanceof Element ? [elements] : elements;

  nodeList.forEach((el) => {
    if (el) {
      el.classList.add(className);
    }
  });
}

/**
 * Remove class from element(s)
 * @param {Element|NodeList|string} target - Element, NodeList, or selector
 * @param {string} className - Class name to remove
 * @param {Element} context - Context for selector
 */
export function removeClass(target, className, context = document) {
  const elements = typeof target === 'string' ? $(target, context) : target;
  const nodeList = elements instanceof Element ? [elements] : elements;

  nodeList.forEach((el) => {
    if (el) {
      el.classList.remove(className);
    }
  });
}

/**
 * Toggle class on element(s)
 * @param {Element|NodeList|string} target - Element, NodeList, or selector
 * @param {string} className - Class name to toggle
 * @param {Element} context - Context for selector
 */
export function toggleClass(target, className, context = document) {
  const elements = typeof target === 'string' ? $(target, context) : target;
  const nodeList = elements instanceof Element ? [elements] : elements;

  nodeList.forEach((el) => {
    if (el) {
      el.classList.toggle(className);
    }
  });
}

/**
 * Check if element has class
 * @param {Element} element - Element to check
 * @param {string} className - Class name
 * @returns {boolean}
 */
export function hasClass(element, className) {
  return element && element.classList.contains(className);
}

/**
 * Get/Set attribute
 * @param {Element} element - Element
 * @param {string} name - Attribute name
 * @param {string} [value] - Attribute value (if setting)
 * @returns {string|null}
 */
export function attr(element, name, value) {
  if (!element) return null;
  if (value !== undefined) {
    element.setAttribute(name, value);
    return value;
  }
  return element.getAttribute(name);
}

/**
 * Remove attribute
 * @param {Element} element - Element
 * @param {string} name - Attribute name
 */
export function removeAttr(element, name) {
  if (element) {
    element.removeAttribute(name);
  }
}

/**
 * Get/Set data attribute
 * @param {Element} element - Element
 * @param {string} name - Data attribute name (without 'data-' prefix)
 * @param {string} [value] - Data attribute value (if setting)
 * @returns {string|null}
 */
export function data(element, name, value) {
  if (!element) return null;
  if (value !== undefined) {
    element.dataset[name] = value;
    return value;
  }
  return element.dataset[name] || null;
}

/**
 * Get/Set HTML content
 * @param {Element} element - Element
 * @param {string} [html] - HTML content (if setting)
 * @returns {string}
 */
export function html(element, html) {
  if (!element) return '';
  if (html !== undefined) {
    element.innerHTML = html;
    return html;
  }
  return element.innerHTML;
}

/**
 * Get/Set text content
 * @param {Element} element - Element
 * @param {string} [text] - Text content (if setting)
 * @returns {string}
 */
export function text(element, text) {
  if (!element) return '';
  if (text !== undefined) {
    element.textContent = text;
    return text;
  }
  return element.textContent;
}

/**
 * Get/Set value
 * @param {Element} element - Element
 * @param {string} [value] - Value (if setting)
 * @returns {string}
 */
export function val(element, value) {
  if (!element) return '';
  if (value !== undefined) {
    element.value = value;
    return value;
  }
  return element.value;
}

/**
 * Append child element or HTML
 * @param {Element} parent - Parent element
 * @param {Element|string} child - Child element or HTML string
 */
export function append(parent, child) {
  if (!parent) return;
  if (typeof child === 'string') {
    parent.insertAdjacentHTML('beforeend', child);
  } else {
    parent.appendChild(child);
  }
}

/**
 * Prepend child element or HTML
 * @param {Element} parent - Parent element
 * @param {Element|string} child - Child element or HTML string
 */
export function prepend(parent, child) {
  if (!parent) return;
  if (typeof child === 'string') {
    parent.insertAdjacentHTML('afterbegin', child);
  } else {
    parent.insertBefore(child, parent.firstChild);
  }
}

/**
 * Remove element(s)
 * @param {Element|NodeList|string} target - Element, NodeList, or selector
 * @param {Element} context - Context for selector
 */
export function remove(target, context = document) {
  const elements = typeof target === 'string' ? $(target, context) : target;
  const nodeList = elements instanceof Element ? [elements] : elements;

  nodeList.forEach((el) => {
    if (el && el.parentNode) {
      el.parentNode.removeChild(el);
    }
  });
}

/**
 * Find parent element matching selector
 * @param {Element} element - Starting element
 * @param {string} selector - CSS selector
 * @returns {Element|null}
 */
export function closest(element, selector) {
  return element ? element.closest(selector) : null;
}

/**
 * Show element(s)
 * @param {Element|NodeList|string} target - Element, NodeList, or selector
 * @param {Element} context - Context for selector
 */
export function show(target, context = document) {
  const elements = typeof target === 'string' ? $(target, context) : target;
  const nodeList = elements instanceof Element ? [elements] : elements;

  nodeList.forEach((el) => {
    if (el) {
      el.style.display = '';
    }
  });
}

/**
 * Hide element(s)
 * @param {Element|NodeList|string} target - Element, NodeList, or selector
 * @param {Element} context - Context for selector
 */
export function hide(target, context = document) {
  const elements = typeof target === 'string' ? $(target, context) : target;
  const nodeList = elements instanceof Element ? [elements] : elements;

  nodeList.forEach((el) => {
    if (el) {
      el.style.display = 'none';
    }
  });
}

/**
 * Trigger event on element
 * @param {Element} element - Element
 * @param {string} eventName - Event name
 */
export function trigger(element, eventName) {
  if (!element) return;
  const event = new Event(eventName, { bubbles: true });
  element.dispatchEvent(event);
}

/**
 * Ajax request helper
 * @param {string} url - URL to fetch
 * @param {Object} options - Fetch options
 * @returns {Promise}
 */
export function ajax(url, options = {}) {
  const defaults = {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  };

  return fetch(url, { ...defaults, ...options }).then((response) => {
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  });
}

/**
 * DOM ready helper
 * @param {Function} callback - Function to call when DOM is ready
 */
export function ready(callback) {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', callback);
  } else {
    callback();
  }
}

/**
 * Debounce function
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function}
 */
export function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Throttle function
 * @param {Function} func - Function to throttle
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function}
 */
export function throttle(func, wait) {
  let timeout;
  let lastRan;
  return function executedFunction(...args) {
    if (!lastRan) {
      func(...args);
      lastRan = Date.now();
    } else {
      clearTimeout(timeout);
      timeout = setTimeout(
        () => {
          if (Date.now() - lastRan >= wait) {
            func(...args);
            lastRan = Date.now();
          }
        },
        wait - (Date.now() - lastRan)
      );
    }
  };
}

/**
 * Cookie utilities
 */
export const cookie = {
  /**
   * Get cookie value
   * @param {string} name - Cookie name
   * @returns {string|null}
   */
  get(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
      return parts.pop().split(';').shift();
    }
    return null;
  },

  /**
   * Set cookie
   * @param {string} name - Cookie name
   * @param {string} value - Cookie value
   * @param {number} days - Expiration in days
   */
  set(name, value, days = 365) {
    let expires = '';
    if (days) {
      const date = new Date();
      date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
      expires = `; expires=${date.toUTCString()}`;
    }
    document.cookie = `${name}=${value || ''}${expires}; path=/`;
  },

  /**
   * Delete cookie
   * @param {string} name - Cookie name
   */
  delete(name) {
    this.set(name, '', -1);
  },
};
