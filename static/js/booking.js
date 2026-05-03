/**
 * Populate doctors by department + calendar (flatpickr) for booking UI
 */
document.addEventListener("DOMContentLoaded", () => {
  const shell = document.querySelector("[data-presel-doctor]");
  const presel = shell?.getAttribute("data-presel-doctor")?.trim();

  const deptSel = document.getElementById("bookingDepartment");
  const docSel = document.getElementById("bookingDoctor");
  const dateEl = document.getElementById("appointment_date");
  if (!deptSel || !docSel) return;

  const loadDoctors = () => {
    const dept = deptSel.value;
    docSel.innerHTML = '<option value="">Select doctor…</option>';
    if (!dept) return;
    const url = `/api/doctors/by-department?department=${encodeURIComponent(dept)}`;
    fetch(url, { headers: { Accept: "application/json" } })
      .then((r) => r.json())
      .then((rows) => {
        rows.forEach((row) => {
          const opt = document.createElement("option");
          opt.value = row.id;
          opt.textContent = row.name;
          docSel.appendChild(opt);
        });
        if (presel) docSel.value = presel;
      })
      .catch(() => {
        docSel.innerHTML += '<option value="" disabled>Error loading clinicians</option>';
      });
  };

  deptSel.addEventListener("change", loadDoctors);
  loadDoctors();

  if (dateEl && window.flatpickr) {
    flatpickr(dateEl, {
      minDate: "today",
      dateFormat: "Y-m-d",
      disableMobile: true,
      animate: window.matchMedia && !window.matchMedia("(prefers-reduced-motion: reduce)").matches,
    });
  }
});
