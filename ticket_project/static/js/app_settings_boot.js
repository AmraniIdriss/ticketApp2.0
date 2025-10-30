// static/js/app_settings_boot.js
(function () {
  var PREFIX = 'app.settings';

  // Valeurs par défaut (mêmes clés que ton settings.js)
  var DEFAULTS = {
    theme: 'auto',
    fontSize: 'normal',
    contrast: 'off',
    density: 'normal',
    fontFamily: 'system-ui',
    language: 'fr'
  };

  function get(key) {
    var v = localStorage.getItem(PREFIX + '.' + key);
    return v !== null ? v : DEFAULTS[key];
  }

  var st = {
    theme: get('theme'),
    fontSize: get('fontSize'),
    contrast: get('contrast'),
    density: get('density'),
    fontFamily: get('fontFamily'),
    language: get('language')
  };

  // Résolution "auto" → light/dark réel
  var prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  var effectiveTheme = (st.theme === 'auto') ? (prefersDark ? 'dark' : 'light') : st.theme;

  var html = document.documentElement;
  html.setAttribute('data-theme', effectiveTheme);     // 'light' | 'dark'
  html.setAttribute('data-contrast', st.contrast);     // 'off' | 'high'
  html.setAttribute('data-density', st.density);       // 'normal' | 'compact'
  html.setAttribute('lang', st.language || 'fr');

  // Font size + family en variables globales (que ton CSS doit consommer)
  var SIZE = { small:'14px', normal:'16px', large:'18px', xlarge:'20px' }[st.fontSize] || '16px';
  var FAMILY = {
    'system-ui': 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    'serif': 'Georgia, "Times New Roman", Times, serif',
    'monospace': '"Courier New", Courier, monospace',
    'cursive': 'cursive'
  }[st.fontFamily] || 'system-ui, -apple-system, Segoe UI, Roboto, sans-serif';

  html.style.setProperty('--font-size-base', SIZE);
  html.style.setProperty('--font-family', FAMILY);

  // Suivre le système si theme=auto (facultatif)
  try {
    var mq = window.matchMedia('(prefers-color-scheme: dark)');
    mq.addEventListener && mq.addEventListener('change', function () {
      if ((localStorage.getItem(PREFIX + '.theme') || 'auto') === 'auto') {
        var dark = mq.matches;
        html.setAttribute('data-theme', dark ? 'dark' : 'light');
      }
    });
  } catch (_) {}
})();
