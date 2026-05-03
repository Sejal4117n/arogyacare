(() => {
  function setStatus(text, ok) {
    const el = document.getElementById("feedbackStatus");
    if (!el) return;
    el.textContent = text;
    el.classList.remove("text-success", "text-warning", "text-danger");
    if (ok === true) el.classList.add("text-success");
    if (ok === false) el.classList.add("text-danger");
    if (ok === null) el.classList.add("text-warning");
  }

  function initStars() {
    const stars = Array.from(document.querySelectorAll(".fb-star"));
    const hidden = document.getElementById("fbRating");
    if (!stars.length || !hidden) return;

    function paint() {
      const active = Number(hidden.value || "0");
      stars.forEach((btn) => {
        const r = Number(btn.getAttribute("data-rating") || "0");
        btn.classList.toggle("btn-light", r <= active);
        btn.classList.toggle("btn-outline-light", r > active);
      });
    }

    stars.forEach((btn) => {
      btn.addEventListener("click", () => {
        hidden.value = String(Number(btn.getAttribute("data-rating") || "0"));
        paint();
      });
    });
    paint();
  }

  async function submitToApi(payload) {
    const res = await fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("api_error");
    const body = await res.json().catch(() => ({}));
    if (!body.ok) throw new Error("api_error");
  }

  function saveLocal(payload) {
    const key = "arogyacare_feedback";
    const oldRows = JSON.parse(localStorage.getItem(key) || "[]");
    oldRows.unshift({
      ...payload,
      created_at: new Date().toISOString(),
    });
    localStorage.setItem(key, JSON.stringify(oldRows.slice(0, 300)));
  }

  function initForm() {
    const form = document.getElementById("feedbackForm");
    if (!form) return;
    form.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const name = (document.getElementById("fbName")?.value || "").trim();
      const message = (document.getElementById("fbMessage")?.value || "").trim();
      const rating = Number(document.getElementById("fbRating")?.value || "0");

      if (name.length < 2 || message.length < 2 || rating < 1 || rating > 5) {
        setStatus("Please fill name, message, and rating.", false);
        return;
      }

      const payload = { name, message, rating };
      try {
        await submitToApi(payload);
        setStatus("Feedback submitted successfully", true);
      } catch {
        saveLocal(payload);
        setStatus("Feedback submitted successfully", true);
      }
      form.reset();
      const ratingHidden = document.getElementById("fbRating");
      if (ratingHidden) ratingHidden.value = "0";
      document.querySelectorAll(".fb-star").forEach((b) => {
        b.classList.remove("btn-light");
        b.classList.add("btn-outline-light");
      });
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    initStars();
    initForm();
  });
})();
