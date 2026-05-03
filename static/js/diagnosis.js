/**
 * Diagnosis hub — open modals & POST JSON payloads to Flask.
 */
(function () {
  const modalMap = {
    heart: "#modalHeart",
    diabetes: "#modalDiabetes",
    thyroid: "#modalThyroid",
  };

  const formMap = {
    heart: "formHeart",
    diabetes: "formDiabetes",
    thyroid: "formThyroid",
  };

  const numericFieldNames = new Set([
    "age",
    "sex",
    "cp",
    "trestbps",
    "chol",
    "fbs",
    "restecg",
    "thalach",
    "exang",
    "oldpeak",
    "slope",
    "ca",
    "thal",
    "glucose",
    "bp",
    "skinthickness",
    "insulin",
    "bmi",
    "dpf",
    "tsh",
  ]);

  function cfgUrl() {
    const tag = document.getElementById("diagSubmitUrl");
    if (!tag) return "";
    try {
      return JSON.parse(tag.textContent);
    } catch {
      return "";
    }
  }

  function modalForm(modalEl) {
    return modalEl ? modalEl.querySelector("form") : null;
  }

  function resultBox(form) {
    return form ? form.querySelector(".diag-result") : null;
  }

  function setResult(box, variant, html) {
    if (!box) return;
    box.classList.remove("d-none", "alert-success", "alert-danger", "alert-info");
    box.classList.add("alert-" + variant);
    box.innerHTML = html;
    box.classList.remove("d-none");
  }

  function buildPayload(testType, form) {
    const fd = new FormData(form);
    const payload = { test_type: testType };

    fd.forEach((val, key) => {
      if (key === "test_type") return;
      if (numericFieldNames.has(key)) {
        const n = Number(val);
        payload[key] = Number.isFinite(n) ? n : val;
      } else {
        payload[key] = val === "yes" || val === "no" ? val : val;
      }
    });
    return payload;
  }

  async function handleSubmit(ev, testType) {
    ev.preventDefault();
    const form = ev.currentTarget;
    const box = resultBox(form);
    const submitUrl = cfgUrl();
    if (!submitUrl) {
      setResult(box, "danger", "<strong>Error</strong> · Missing submission URL.");
      return;
    }

    const payload = buildPayload(testType, form);
    setResult(box, "info", "Sending…");

    try {
      const res = await fetch(submitUrl, {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok || !body.ok) {
        const msg =
          typeof body.error === "string"
            ? body.error
            : "Could not evaluate — fill every field with valid numbers.";
        setResult(box, "danger", "<strong>Something went wrong</strong> · " + msg);
        return;
      }

      var tierClass = "info";
      if (body.result && body.result.includes("Low")) tierClass = "success";
      if (body.result && body.result.includes("High")) tierClass = "danger";
      if (body.result && body.result.includes("Medium")) tierClass = "warning";

      setResult(
        box,
        tierClass === "success" ? "success" : tierClass === "danger" ? "danger" : tierClass === "warning" ? "warning" : "info",
        [
          '<div class="d-flex gap-3 align-items-start">',
          '<div class="fs-4 fw-black text-dark-emphasis flex-shrink-0">' + escapeHtml(body.score) + "</div>",
          "<div>",
          '<div class="small text-muted">' + escapeHtml(body.test_label || "") + "</div>",
          '<div class="fw-bold">' + escapeHtml(body.result || "") + "</div>",
          '<div class="small mt-2 text-muted">Saved · your dashboard and care team lists will show this after refresh.</div>',
          "</div></div>",
        ].join(""),
      );

      try {
        form.reset();
      } catch {
        /* ignore */
      }
    } catch (e) {
      setResult(box, "danger", "<strong>Network</strong> · Check connection and try again.");
    }
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/"/g, "&quot;");
  }

  function wire() {
    document.querySelectorAll("[data-diag-modal]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const key = btn.getAttribute("data-diag-modal");
        const sel = modalMap[key];
        if (!sel || typeof bootstrap === "undefined") return;
        const el = document.querySelector(sel);
        if (!el) return;
        const inst = bootstrap.Modal.getOrCreateInstance(el);
        inst.show();
      });
    });

    Object.entries(formMap).forEach(([type, fid]) => {
      const form = document.getElementById(fid);
      if (form) form.addEventListener("submit", (ev) => handleSubmit(ev, type));
    });

    ["modalHeart", "modalDiabetes", "modalThyroid"].forEach((mid) => {
      const modalEl = document.getElementById(mid);
      if (!modalEl) return;
      modalEl.addEventListener("hidden.bs.modal", () => {
        const fm = modalForm(modalEl);
        const rb = resultBox(fm);
        if (fm) fm.reset();
        if (rb) {
          rb.classList.add("d-none");
          rb.innerHTML = "";
          rb.classList.remove("alert-success", "alert-danger", "alert-info", "alert-warning");
        }
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", wire);
  } else {
    wire();
  }
})();
