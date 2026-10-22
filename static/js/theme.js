(() => {
  const root = document.documentElement;
  const button = document.getElementById('themeToggle');
  const saved = localStorage.getItem('sicap-theme') || 'light';
  root.dataset.theme = saved;
  function label() { if (!button) return; const dark = root.dataset.theme === 'dark'; button.querySelector('.theme-label').textContent = dark ? 'Modo claro' : 'Modo oscuro'; button.setAttribute('aria-pressed', String(dark)); }
  label();
  button?.addEventListener('click', () => { root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark'; localStorage.setItem('sicap-theme', root.dataset.theme); label(); });
})();
