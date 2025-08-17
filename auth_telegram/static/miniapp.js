(function () {
  const app = document.getElementById('app');
  const tg = window.Telegram && window.Telegram.WebApp;
  if (!tg?.initDataUnsafe?.user) {
    app.innerHTML = '<p>This page is only available via Telegram.</p>' +
      '<p><a href="https://t.me/your_bot?startapp">Open via Bot</a></p>';
    return;
  }
  tg.ready();
  tg.expand();
  fetch('/api/auth/telegram/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ init_data: tg.initData }),
    credentials: 'include'
  })
    .then(res => res.json())
    .then(data => {
      if (data.access) {
        localStorage.setItem('access', data.access);
        window.location.href = '/telegram/recipes/';
      } else {
        app.textContent = 'Authentication failed';
      }
    })
    .catch(() => { app.textContent = 'Network error'; });
})();
