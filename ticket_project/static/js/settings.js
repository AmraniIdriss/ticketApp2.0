/*
 * MANUAL TESTS (Checklist)
 * 
 * ✓ Change theme → colors change instantly
 * ✓ Change text size → body and preview follow
 * ✓ Enable contrast → WCAG AA ratio visible
 * ✓ Compact density → paddings reduced by 25%
 * ✓ Refresh page → preferences restored correctly
 * ✓ Reset → everything returns to default values
 * ✓ Auto theme → follows prefers-color-scheme
 * ✓ Font change → text changes immediately
 * ✓ Language → value saved (no real i18n)
 * ✓ Keyboard navigation → all controls accessible
 */

(function() {
    'use strict';

    // ==========================================
    // CONSTANTS
    // ==========================================
    const STORAGE_PREFIX = 'app.settings';
    
    const DEFAULTS = {
        theme: 'auto',
        fontSize: 'normal',
        contrast: 'off',
        density: 'normal',
        fontFamily: 'system-ui',
        language: 'fr'
    };

    const FONT_SIZE_MAP = {
        small: '14px',
        normal: '16px',
        large: '18px',
        xlarge: '20px'
    };

    const FONT_FAMILY_MAP = {
        'system-ui': 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        'serif': 'Georgia, "Times New Roman", Times, serif',
        'monospace': '"Courier New", Courier, monospace',
        'cursive': 'cursive'
    };

    // ==========================================
    // STORAGE UTILITIES
    // ==========================================
    
    /**
     * Loads settings from localStorage with fallback to defaults
     * @returns {Object} Complete settings
     */
    function loadSettings() {
        const settings = { ...DEFAULTS };
        
        Object.keys(DEFAULTS).forEach(key => {
            const storageKey = `${STORAGE_PREFIX}.${key}`;
            const stored = localStorage.getItem(storageKey);
            if (stored !== null) {
                settings[key] = stored;
            }
        });
        
        return settings;
    }

    /**
     * Saves settings to localStorage
     * @param {Object} settings - Settings to save
     */
    function saveToStorage(settings) {
        Object.keys(settings).forEach(key => {
            const storageKey = `${STORAGE_PREFIX}.${key}`;
            localStorage.setItem(storageKey, settings[key]);
        });
    }

    /**
     * Saves a partial change and reapplies
     * @param {Object} partial - Partial changes
     */
    function saveSettings(partial) {
        const current = loadSettings();
        const updated = { ...current, ...partial };
        saveToStorage(updated);
        applySettings(updated);
    }

    /**
     * Restores default settings
     */
    function resetSettings() {
        saveToStorage(DEFAULTS);
        applySettings(DEFAULTS);
        syncFormInputs(DEFAULTS);
    }

    // ==========================================
    // APPLYING SETTINGS
    // ==========================================
    
    /**
     * Applies all settings to DOM and CSS
     * @param {Object} settings - Settings to apply
     */
    function applySettings(settings) {
        const html = document.documentElement;
        
        // Theme
        html.setAttribute('data-theme', settings.theme);
        
        // Contrast
        html.setAttribute('data-contrast', settings.contrast);
        
        // Density
        html.setAttribute('data-density', settings.density);
        
        // Font size
        const fontSize = FONT_SIZE_MAP[settings.fontSize] || FONT_SIZE_MAP.normal;
        html.style.setProperty('--font-size-base', fontSize);
        
        // Font family
        const fontFamily = FONT_FAMILY_MAP[settings.fontFamily] || FONT_FAMILY_MAP['system-ui'];
        html.style.setProperty('--font-family', fontFamily);
        
        // Language (stored but no real i18n)
        html.setAttribute('lang', settings.language);
    }

    /**
     * Syncs form inputs with settings
     * @param {Object} settings - Current settings
     */
    function syncFormInputs(settings) {
        // Radios and selects
        Object.keys(settings).forEach(key => {
            const input = document.querySelector(`[name="${key}"]`);
            if (!input) return;
            
            if (input.type === 'radio') {
                const radioToCheck = document.querySelector(`[name="${key}"][value="${settings[key]}"]`);
                if (radioToCheck) radioToCheck.checked = true;
            } else if (input.tagName === 'SELECT') {
                input.value = settings[key];
            }
        });
        
        // Contrast toggle
        const contrastToggle = document.getElementById('contrast');
        if (contrastToggle) {
            contrastToggle.checked = settings.contrast === 'high';
            contrastToggle.setAttribute('aria-checked', settings.contrast === 'high');
        }
    }

    // ==========================================
    // EVENT HANDLERS
    // ==========================================
    
    /**
     * Sets up all event listeners
     */
    function setupEventListeners() {
        // Radios (theme, fontSize, density)
        document.querySelectorAll('input[type="radio"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                const name = e.target.name;
                const value = e.target.value;
                saveSettings({ [name]: value });
            });
        });
        
        // Contrast toggle
        const contrastToggle = document.getElementById('contrast');
        if (contrastToggle) {
            contrastToggle.addEventListener('change', (e) => {
                const value = e.target.checked ? 'high' : 'off';
                e.target.setAttribute('aria-checked', e.target.checked);
                saveSettings({ contrast: value });
            });
        }
        
        // Selects (fontFamily, language)
        document.querySelectorAll('select').forEach(select => {
            select.addEventListener('change', (e) => {
                const name = e.target.name;
                const value = e.target.value;
                saveSettings({ [name]: value });
            });
        });
        
        // Reset button
        const resetBtn = document.getElementById('resetBtn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                if (confirm('Do you really want to restore all settings to default?')) {
                    resetSettings();
                }
            });
        }
    }

    // ==========================================
    // INITIALIZATION
    // ==========================================
    
    /**
     * Main entry point
     */
    function init() {
        // Load and apply immediately to avoid FOUC
        const settings = loadSettings();
        applySettings(settings);
        syncFormInputs(settings);
        
        // Mark as ready (opacity transition)
        document.body.classList.add('js-ready');
        
        // Set up events
        setupEventListeners();
        
        console.log('✓ Settings loaded:', settings);
    }

    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Expose some functions for debugging (optional)
    window.appSettings = {
        load: loadSettings,
        save: saveSettings,
        reset: resetSettings,
        apply: applySettings
    };

})();