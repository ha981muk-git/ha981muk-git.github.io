// Dark Mode Toggle
function initializeDarkMode() {
    const toggle = document.createElement('button');
    toggle.className = 'dark-mode-toggle';
    toggle.innerHTML = '🌓';
    toggle.setAttribute('aria-label', 'Toggle dark mode');
    toggle.setAttribute('tabindex', '0');
    
    // Check system preference and localStorage
    const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const savedTheme = localStorage.getItem('theme');
    
    if ((systemDark && !savedTheme) || savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        toggle.innerHTML = '☀️';
    }

    // Toggle functionality
    function toggleTheme() {
        document.body.classList.toggle('dark-mode');
        const isDark = document.body.classList.contains('dark-mode');
        toggle.innerHTML = isDark ? '☀️' : '🌓';
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    }

    // Event listeners
    toggle.addEventListener('click', toggleTheme);
    toggle.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') toggleTheme();
    });

    document.body.appendChild(toggle);
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeDarkMode);