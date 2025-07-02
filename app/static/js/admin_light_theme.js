/**
 * Admin Light Theme Override JavaScript
 * 
 * This script forces the Django admin interface to always use light theme
 * by overriding the theme cycling functionality and localStorage settings.
 */

(function() {
    'use strict';
    
    let isApplyingTheme = false; // Prevent infinite loops
    
    // Force light theme on page load
    function forceThemeLight() {
        if (isApplyingTheme) return; // Prevent recursion
        
        isApplyingTheme = true;
        
        try {
            // Set theme to light in localStorage
            localStorage.setItem('theme', 'light');
            
            // Remove any dark theme classes from document
            document.documentElement.classList.remove('theme-dark');
            document.documentElement.classList.add('theme-light');
            
            // Set data attributes for light theme
            document.documentElement.setAttribute('data-theme', 'light');
            
            // Force color-scheme to light
            document.documentElement.style.colorScheme = 'light';
            
            console.log('Admin theme forced to light mode');
        } catch (error) {
            console.error('Error applying light theme:', error);
        } finally {
            isApplyingTheme = false;
        }
    }
    
    // Override the cycleTheme function if it exists
    function overrideCycleTheme() {
        // Override cycleTheme function
        if (typeof window.cycleTheme === 'function') {
            window.cycleTheme = function() {
                console.log('Theme cycling disabled - staying in light mode');
                forceThemeLight();
            };
        }
        
        // Override setTheme function
        if (typeof window.setTheme === 'function') {
            window.setTheme = function(theme) {
                console.log('setTheme called with:', theme, '- forcing light mode');
                forceThemeLight();
            };
        }
        
        // Try to override after a delay in case functions are loaded later
        setTimeout(function() {
            if (typeof window.cycleTheme === 'function') {
                window.cycleTheme = function() {
                    console.log('Theme cycling disabled - staying in light mode');
                    forceThemeLight();
                };
            }
            
            if (typeof window.setTheme === 'function') {
                window.setTheme = function(theme) {
                    console.log('setTheme called with:', theme, '- forcing light mode');
                    forceThemeLight();
                };
            }
        }, 500);
    }
    
    // Hide theme toggle buttons
    function hideThemeToggles() {
        const selectors = [
            '.theme-toggle',
            '[data-theme-toggle]',
            '.theme-chooser',
            'button[data-theme-toggle]'
        ];
        
        selectors.forEach(function(selector) {
            const elements = document.querySelectorAll(selector);
            elements.forEach(function(el) {
                el.style.display = 'none';
                el.disabled = true;
            });
        });
    }
    
    // Initialize the light theme override
    function initialize() {
        forceThemeLight();
        overrideCycleTheme();
        hideThemeToggles();
        
        // Watch for localStorage changes from other tabs/windows
        window.addEventListener('storage', function(e) {
            if (e.key === 'theme' && e.newValue !== 'light') {
                forceThemeLight();
            }
        });
        
        // Re-check theme periodically (less frequent to avoid performance issues)
        let checkCount = 0;
        const maxChecks = 10; // Stop after 10 checks to prevent infinite running
        
        const intervalId = setInterval(function() {
            checkCount++;
            
            if (checkCount >= maxChecks) {
                clearInterval(intervalId);
                console.log('Light theme enforcement checks completed');
                return;
            }
            
            if (localStorage.getItem('theme') !== 'light') {
                forceThemeLight();
            }
            hideThemeToggles();
        }, 2000); // Check every 2 seconds instead of 1
    }
    
    // Run initialization
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
    
    // Also run on window load to catch late-loaded scripts
    window.addEventListener('load', function() {
        setTimeout(function() {
            overrideCycleTheme();
            forceThemeLight();
            hideThemeToggles();
        }, 200);
    });
    
})();
