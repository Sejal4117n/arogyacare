/**
 * Role tabs (Patient / Doctor / Admin), portal field sync, password visibility
 */
document.addEventListener("DOMContentLoaded", () => {
  const tabs = Array.from(document.querySelectorAll("[data-role-tab]"));
  const portalInput = document.querySelector('input[name="portal"]');

  const setActivePortal = (role) => {
    tabs.forEach((btn) => {
      const r = btn.getAttribute("data-role-tab");
      const active = r === role;
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-selected", active ? "true" : "false");
    });
    if (portalInput) portalInput.value = role;
  };

  tabs.forEach((btn) => {
    btn.addEventListener("click", () => setActivePortal(btn.getAttribute("data-role-tab")));
  });

  document.querySelectorAll("[data-eye-toggle]").forEach((wrapper) => {
    const inp = wrapper.querySelector("input.form-control[type='password'], input.form-control[type='text']");
    const btn = wrapper.querySelector("[data-eye]");
    const shownIcon = wrapper.querySelector("[data-icon-show]");
    const hiddenIcon = wrapper.querySelector("[data-icon-hide]");
    if (!inp || !btn) return;

    const syncGlyph = () => {
      const isText = inp.getAttribute("type") === "text";
      btn.setAttribute("aria-pressed", isText ? "true" : "false");
      if (shownIcon) shownIcon.hidden = isText;
      if (hiddenIcon) hiddenIcon.hidden = !isText;
    };

    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const next = inp.getAttribute("type") === "password" ? "text" : "password";
      inp.setAttribute("type", next);
      syncGlyph();
      inp.focus();
    });

    syncGlyph();
  });

  const seeded = portalInput?.value?.trim().toLowerCase();
  const fromTab =
    tabs.find((b) => b.classList.contains("is-active"))?.getAttribute("data-role-tab") || "patient";

  setActivePortal(seeded && seeded.length ? seeded : fromTab);
});
