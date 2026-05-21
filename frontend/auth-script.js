const API_BASE = "";

const Auth = {
  TOKEN_KEY: "memorium_token",
  USER_KEY: "memorium_user",

  getToken() {
    return localStorage.getItem(this.TOKEN_KEY);
  },

  getUser() {
    const raw = localStorage.getItem(this.USER_KEY);
    return raw ? JSON.parse(raw) : null;
  },

  save(token, user) {
    localStorage.setItem(this.TOKEN_KEY, token);
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  },

  clear() {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  },

  isLoggedIn() {
    return !!this.getToken();
  },

  authHeaders() {
    const token = this.getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  },

  async apiFetch(url, options = {}) {
    const headers = {
      "Content-Type": "application/json",
      ...this.authHeaders(),
      ...(options.headers || {}),
    };
    const res = await fetch(API_BASE + url, { ...options, headers });
    if (res.status === 401) {
      this.clear();
      updateAuthUI();
    }
    return res;
  },
};

async function loginUser(username, password) {
  const body = new URLSearchParams({ username, password });
  const res = await fetch(API_BASE + "/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Ошибка входа");

  Auth.save(data.access_token, data.user);
  return data.user;
}

async function registerUser(username, email, password, displayName) {
  const res = await fetch(API_BASE + "/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username,
      email,
      password,
      display_name: displayName || undefined,
    }),
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Ошибка регистрации");

  Auth.save(data.access_token, data.user);
  return data.user;
}

function updateAuthUI() {
  const btn = document.getElementById("authBtn");
  if (!btn) return;

  const user = Auth.getUser();

  if (user) {
    const initial = (user.display_name ||
      user.username ||
      "?")[0].toUpperCase();
    btn.innerHTML = `
      <div class="auth-user-info">
        <div class="auth-avatar">${initial}</div>
        <span>${user.display_name || user.username}</span>
        <button class="auth-logout-btn" id="logoutBtn">Выйти</button>
      </div>`;
    document.getElementById("logoutBtn")?.addEventListener("click", (e) => {
      e.stopPropagation();
      Auth.clear();
      updateAuthUI();
    });
  } else {
    btn.innerHTML = '<i class="far fa-user-circle"></i> Войти';
  }
}

function openAuthModal(tab = "login") {
  const overlay = document.getElementById("authOverlay");
  if (!overlay) return;
  overlay.classList.add("active");
  switchTab(tab);
  clearErrors();
}

function closeAuthModal() {
  document.getElementById("authOverlay")?.classList.remove("active");
  clearErrors();
}

function switchTab(tab) {
  document.querySelectorAll(".auth-tab-btn").forEach((b) => {
    b.classList.toggle("active", b.dataset.tab === tab);
  });
  document.getElementById("loginForm").style.display =
    tab === "login" ? "flex" : "none";
  document.getElementById("registerForm").style.display =
    tab === "register" ? "flex" : "none";
}

function clearErrors() {
  ["loginError", "registerError"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.textContent = "";
  });
}

function setLoading(btnId, loading) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  btn.disabled = loading;
  btn.textContent = loading
    ? btnId === "loginBtn"
      ? "Входим..."
      : "Создаём..."
    : btnId === "loginBtn"
      ? "Войти"
      : "Создать аккаунт";
}

function initAuth() {
  fetch("/auth-component.html")
    .then((r) => r.text())
    .then((html) => {
      document.body.insertAdjacentHTML("beforeend", html);
      bindAuthEvents();
      updateAuthUI();
    })
    .catch(() => {
      bindAuthEvents();
      updateAuthUI();
    });
}

function bindAuthEvents() {
  const authBtn = document.getElementById("authBtn");
  if (authBtn) {
    authBtn.addEventListener("click", () => {
      if (!Auth.isLoggedIn()) openAuthModal("login");
    });
  }

  document
    .getElementById("authClose")
    ?.addEventListener("click", closeAuthModal);

  document.getElementById("authOverlay")?.addEventListener("click", (e) => {
    if (e.target.id === "authOverlay") closeAuthModal();
  });

  document.querySelectorAll(".auth-tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      switchTab(btn.dataset.tab);
      clearErrors();
    });
  });

  document
    .getElementById("loginForm")
    ?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const username = document.getElementById("loginUsername").value.trim();
      const password = document.getElementById("loginPassword").value;
      const errorEl = document.getElementById("loginError");

      setLoading("loginBtn", true);
      errorEl.textContent = "";

      try {
        await loginUser(username, password);
        closeAuthModal();
        updateAuthUI();
      } catch (err) {
        errorEl.textContent = err.message;
      } finally {
        setLoading("loginBtn", false);
      }
    });

  document
    .getElementById("registerForm")
    ?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const username = document.getElementById("regUsername").value.trim();
      const email = document.getElementById("regEmail").value.trim();
      const displayName = document
        .getElementById("regDisplayName")
        .value.trim();
      const password = document.getElementById("regPassword").value;
      const errorEl = document.getElementById("registerError");

      setLoading("registerBtn", true);
      errorEl.textContent = "";

      try {
        await registerUser(username, email, password, displayName);
        closeAuthModal();
        updateAuthUI();
      } catch (err) {
        errorEl.textContent = err.message;
      } finally {
        setLoading("registerBtn", false);
      }
    });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeAuthModal();
  });
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("authOverlay")) {
    bindAuthEvents();
    updateAuthUI();
  } else {
    initAuth();
  }
});
