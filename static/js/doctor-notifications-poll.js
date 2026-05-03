/**
 * Polls unread + latest inbox rows for the signed-in clinician every 10s.
 */
(() => {
  const POLL_MS = 10000;
  let pollCompletedOnce = false;

  function readCfg(root) {
    const el = document.getElementById("doctorNotifCfg");
    if (!el || !root) return null;
    try {
      const raw = JSON.parse(el.textContent || "{}");
      if (typeof raw.pollUrl === "string" && typeof raw.readUrl === "string") {
        return raw;
      }
    } catch {
      /* ignore */
    }
    return null;
  }

  async function jsonPost(url, body) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    return { ok: res.ok, data };
  }

  function render(root, unreadCount, items) {
    const bell = root.querySelector(".doctor-notif-bell-btn");
    const badge = root.querySelector("[data-doctor-notif-badge]");
    const list = root.querySelector(".doctor-notif-list");
    const emptyEl = root.querySelector(".doctor-notif-empty");
    const teaser = root.querySelector("[data-doctor-notif-teaser]");

    if (!list) return;

    if (badge) {
      const n = Math.max(0, Number(unreadCount) || 0);
      badge.textContent = n > 99 ? "99+" : String(n);
      badge.hidden = n === 0;
      if (n === 0) badge.removeAttribute("aria-label");
      else badge.setAttribute("aria-label", `${n} unread notifications`);
    }

    if (bell) {
      const n = Number(unreadCount) || 0;
      bell.classList.toggle("doctor-notif-bell-btn--live", n > 0);
    }

    if (teaser) {
      const firstUnread = Array.isArray(items) ? items.find((i) => i && !i.read) : null;
      if (firstUnread && (Number(unreadCount) || 0) > 0) {
        teaser.hidden = false;
        teaser.textContent = firstUnread.title || "New booking notification";
      } else {
        teaser.hidden = true;
      }
    }

    list.innerHTML = "";
    if (!items || !items.length) {
      if (emptyEl) emptyEl.hidden = !pollCompletedOnce;
      return;
    }
    if (emptyEl) emptyEl.hidden = true;

    items.forEach((item) => {
      if (!item) return;
      const li = document.createElement("li");
      li.className = "mb-2";

      const box = document.createElement("div");
      box.className = [
        "dash-notif",
        "doctor-notif-item",
        item.read ? "" : "unread",
        item.emergency ? "doctor-notif-item--emergency" : "",
      ]
        .filter(Boolean)
        .join(" ");

      const titleEl = document.createElement("div");
      titleEl.className = item.emergency ? "fw-bold small text-danger-emphasis" : "fw-bold small";
      titleEl.textContent = item.title || "";

      const meta = document.createElement("div");
      meta.className = "small text-muted";
      try {
        if (item.created_at) meta.textContent = new Date(item.created_at).toLocaleString();
      } catch {
        meta.textContent = "";
      }

      const bodyEl = document.createElement("div");
      bodyEl.className = "small mt-1 doctor-notif-message";
      bodyEl.style.whiteSpace = "pre-line";
      bodyEl.textContent = item.message || item.body || "";

      box.append(titleEl);
      if (meta.textContent) box.append(meta);
      if (bodyEl.textContent) box.append(bodyEl);

      li.append(box);
      list.append(li);
    });
  }

  async function pollOnce(cfg, root, renderFn) {
    try {
      const res = await fetch(cfg.pollUrl, { headers: { Accept: "application/json" } });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) return;
      pollCompletedOnce = true;
      const unread = data.unread_count ?? 0;
      const items = Array.isArray(data.items) ? data.items : [];
      renderFn(root, unread, items);
    } catch {
      /* network errors: leave last UI */
    }
  }

  function initDropdownMarkRead(cfg, root) {
    const dd = root.querySelector(".doctor-notif-dropdown");
    if (!dd || typeof bootstrap === "undefined") return;

    dd.addEventListener("show.bs.dropdown", () => {
      jsonPost(cfg.readUrl, { mark_all: true }).then(({ ok }) => {
        if (ok) pollOnce(cfg, root, render);
      });
    });
  }

  function boot() {
    const root = document.querySelector("[data-doctor-notif-root]");
    const cfg = readCfg(root);
    if (!root || !cfg) return;

    initDropdownMarkRead(cfg, root);
    pollOnce(cfg, root, render).then(() => {});
    window.setInterval(() => {
      pollOnce(cfg, root, render);
    }, POLL_MS);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
