(function () {
    const THEME_KEY = 'hm_theme_preference';
    const LEGACY_THEME_KEY = 'theme';
    const THEME_LIGHT = 'light';
    const THEME_DARK = 'dark';
    const LEGACY_AUTO = 'auto';

    let currentTheme = THEME_LIGHT;
    let hasExplicitPreference = false;
    let picker = null;

    function getSavedTheme() {
        try {
            const saved = localStorage.getItem(THEME_KEY);
            if (saved === THEME_LIGHT || saved === THEME_DARK) {
                hasExplicitPreference = true;
                return saved;
            }

            if (saved === LEGACY_AUTO) {
                localStorage.removeItem(THEME_KEY);
            }

            const legacy = localStorage.getItem(LEGACY_THEME_KEY);
            if (legacy === THEME_LIGHT || legacy === THEME_DARK) {
                localStorage.setItem(THEME_KEY, legacy);
                localStorage.removeItem(LEGACY_THEME_KEY);
                hasExplicitPreference = true;
                return legacy;
            }
        } catch (err) {}

        hasExplicitPreference = false;
        return THEME_LIGHT;
    }

    function saveTheme(theme) {
        try {
            localStorage.setItem(THEME_KEY, theme);
            localStorage.removeItem(LEGACY_THEME_KEY);
        } catch (err) {}
    }

    function applyTheme(themeChoice) {
        const isDark = themeChoice === THEME_DARK;

        document.documentElement.classList.toggle('dark-mode', isDark);
        if (document.body) document.body.classList.toggle('dark-mode', isDark);
    }

    function setTheme(themeChoice) {
        currentTheme = themeChoice;
        hasExplicitPreference = true;
        saveTheme(themeChoice);
        applyTheme(themeChoice);
        syncPicker();
    }

    function syncPicker() {
        if (!picker) return;
        picker.querySelectorAll('.theme-option').forEach((button) => {
            const active = button.getAttribute('data-theme') === currentTheme;
            button.classList.toggle('active', active);
            button.setAttribute('aria-pressed', String(active));
        });
    }

    function createThemeButton(themeValue, iconClass, label) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'theme-option';
        button.setAttribute('data-theme', themeValue);
        button.setAttribute('title', label + ' theme');
        button.setAttribute('aria-label', label + ' theme');
        button.innerHTML = '<i class="' + iconClass + '" aria-hidden="true"></i><span class="sr-only">' + label + ' theme</span>';
        button.addEventListener('click', () => setTheme(themeValue));
        return button;
    }

    function initThemePicker() {
        const host = document.getElementById('dark-mode-container');
        if (!host) return;

        const wrapper = document.createElement('div');
        wrapper.className = 'theme-picker';
        wrapper.setAttribute('role', 'group');
        wrapper.setAttribute('aria-label', 'Theme selector');

        wrapper.appendChild(createThemeButton(THEME_LIGHT, 'fas fa-sun', 'Light'));
        wrapper.appendChild(createThemeButton(THEME_DARK, 'fas fa-moon', 'Dark'));

        host.innerHTML = '';
        host.appendChild(wrapper);
        picker = wrapper;
        syncPicker();
    }

    function initDarkMode() {
        currentTheme = getSavedTheme();
        applyTheme(currentTheme);
        initThemePicker();
    }

    document.addEventListener('DOMContentLoaded', initDarkMode);
})();