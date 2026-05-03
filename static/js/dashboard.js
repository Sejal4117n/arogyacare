/**
 * Dashboard: animated KPI counters + Chart.js line charts from JSON config element
 */
(() => {
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function animateCount(el, end, durationMs) {
    const dec = Number(el.getAttribute("data-decimals") || "0");
    if (reduced) {
      el.textContent = dec > 0 ? end.toFixed(dec) : String(Math.round(end));
      return;
    }
    const start = performance.now();
    const from = 0;

    function fmt(v) {
      if (dec > 0) return v.toFixed(dec);
      return String(Math.round(v));
    }

    function tick(now) {
      const p = Math.min(1, (now - start) / durationMs);
      const eased = 1 - Math.pow(1 - p, 3);
      const val = from + (end - from) * eased;
      el.textContent = fmt(val);
      if (p < 1) requestAnimationFrame(tick);
      else el.textContent = fmt(end);
    }
    requestAnimationFrame(tick);
  }

  function initCounters() {
    document.querySelectorAll("[data-dash-counter]").forEach((el) => {
      const raw = el.getAttribute("data-target");
      if (raw == null || raw === "") return;
      const end = Number(raw);
      if (!Number.isFinite(end)) return;
      const ms = Number(el.getAttribute("data-duration") || "1300");
      animateCount(el, end, reduced ? 0 : ms);
    });
  }

  function lineChartSpec(labels, values, labelText) {
    return {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: labelText,
            data: values,
            fill: true,
            tension: 0.42,
            borderWidth: 2.25,
            pointRadius: 3,
            pointHoverRadius: 5,
            borderColor: "rgba(14, 165, 233, 0.9)",
            backgroundColor(context) {
              const chart = context.chart;
              const { ctx, chartArea } = chart;
              if (!chartArea) return "transparent";
              const g = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
              g.addColorStop(0, "rgba(14, 165, 233, 0.26)");
              g.addColorStop(1, "rgba(16, 185, 129, 0.06)");
              return g;
            },
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: reduced ? false : { duration: 980, easing: "easeOutQuart" },
        interaction: { intersect: false, mode: "index" },
        scales: {
          x: {
            grid: { display: false, drawBorder: false },
            ticks: { color: "rgba(15,23,42,0.45)", font: { size: 11, weight: "600" } },
          },
          y: {
            beginAtZero: true,
            grid: { color: "rgba(148,163,184,0.18)", drawBorder: false },
            ticks: {
              precision: 0,
              color: "rgba(15,23,42,0.45)",
              font: { size: 11, weight: "600" },
            },
          },
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "rgba(15,23,42,0.88)",
            titleFont: { weight: "700", size: 13 },
            bodyFont: { weight: "600", size: 12 },
          },
        },
      },
    };
  }

  function renderChart(canvasId, bundle, datasetLabel) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === "undefined" || !bundle?.labels?.length || !bundle?.values) return null;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;
    return new Chart(ctx, lineChartSpec(bundle.labels, bundle.values, datasetLabel));
  }

  function bootCharts() {
    const el = document.getElementById("dashCharts");
    if (!el) return;
    let parsed;
    try {
      parsed = JSON.parse(el.textContent || "{}");
    } catch {
      return;
    }
    renderChart("chartAppts", parsed.appt_line, "Volume");
    renderChart("chartPred", parsed.pred_line, "Signals");
    renderChart("chartSchedule", parsed.schedule_line, "Workload");
    renderChart("chartCare", parsed.care_line, "Engagements");
  }

  document.addEventListener("DOMContentLoaded", () => {
    initCounters();
    bootCharts();
  });
})();
