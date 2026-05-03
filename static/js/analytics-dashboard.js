(() => {
  function createCard(title, value) {
    return [
      '<div class="col-6 col-md-4 col-xl-3">',
      '<div class="card border-0 shadow-sm h-100"><div class="card-body">',
      `<div class="small text-muted">${title}</div>`,
      `<div class="h4 mb-0">${value}</div>`,
      "</div></div></div>",
    ].join("");
  }

  function renderBarChart(canvasId, labels, values, label) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === "undefined") return;
    new Chart(canvas.getContext("2d"), {
      type: "bar",
      data: {
        labels,
        datasets: [{ label, data: values, borderWidth: 1 }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
        plugins: { legend: { display: false } },
      },
    });
  }

  async function boot() {
    if (!window.analyticsEndpoint) return;
    const res = await fetch(window.analyticsEndpoint, { headers: { Accept: "application/json" } });
    const data = await res.json();
    const cardsEl = document.getElementById("analyticsCards");
    if (!cardsEl) return;

    const p = data.patient_analytics || {};
    const d = data.doctor_analytics || {};
    const a = data.appointment_analytics || {};
    const g = data.diagnosis_analytics || {};
    const b = data.blood_bank_analytics || {};
    const n = data.notification_analytics || {};
    const r = data.report_analytics || {};

    cardsEl.innerHTML =
      createCard("Total Patients", p.total_registered_patients || 0) +
      createCard("New Patients This Month", p.new_patients_this_month || 0) +
      createCard("Total Doctors", d.total_doctors || 0) +
      createCard("Total Appointments", a.total_appointments || 0) +
      createCard("Today's Appointments", a.todays_appointments || 0) +
      createCard("Heart Predictions", g.heart_prediction_count || 0) +
      createCard("Diabetes Predictions", g.diabetes_prediction_count || 0) +
      createCard("Total Donors", b.total_donors || 0) +
      createCard("Notifications Sent", n.total_notifications_sent || 0) +
      createCard("Medical Reports", r.total_medical_reports || 0);

    const dept = a.department_wise_appointments || [];
    renderBarChart(
      "deptChart",
      dept.map((x) => x.department),
      dept.map((x) => x.appointments),
      "Appointments",
    );

    const stock = b.blood_group_wise_stock || [];
    renderBarChart(
      "bloodChart",
      stock.map((x) => x.blood_group),
      stock.map((x) => x.units_available),
      "Units",
    );

    const low = b.low_stock_alerts || [];
    const lowWrap = document.getElementById("lowStockWrap");
    if (lowWrap) {
      if (!low.length) {
        lowWrap.innerHTML = '<p class="text-muted mb-0">No low stock alerts.</p>';
      } else {
        lowWrap.innerHTML = [
          '<table class="table table-sm mb-0"><thead><tr><th>Blood Group</th><th>Units</th><th>Status</th></tr></thead><tbody>',
          ...low.map((x) => `<tr><td>${x.blood_group}</td><td>${x.units_available}</td><td>Low stock</td></tr>`),
          "</tbody></table>",
        ].join("");
      }
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    boot().catch(() => {});
  });
})();
