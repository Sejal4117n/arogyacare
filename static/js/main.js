/**
 * ArogyaCare landing interactions: loader, particles, counters, navbar, AOS, smooth anchors
 */
(() => {
  const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Page loader ---------- */
  const loader = document.getElementById("page-loader");
  function hideLoader() {
    if (!loader) return;
    loader.classList.add("loader-hidden");
    document.body.classList.remove("loader-active");
  }

  document.body.classList.add("loader-active");
  window.addEventListener(
    "load",
    () => {
      window.setTimeout(hideLoader, prefersReduced ? 0 : 480);
    },
    { once: true },
  );

  /* ---------- Navbar glass on scroll ---------- */
  const nav = document.getElementById("landing-navbar");
  function toggleNavGlass() {
    if (!nav) return;
    if (window.scrollY > 12) nav.classList.add("navbar-scrolled");
    else nav.classList.remove("navbar-scrolled");
  }
  toggleNavGlass();
  window.addEventListener("scroll", toggleNavGlass, { passive: true });

  /* ---------- Smooth anchor offset (fixed nav) ---------- */
  document.querySelectorAll('a[data-scroll]').forEach((link) => {
    link.addEventListener("click", (e) => {
      const id = link.getAttribute("href")?.slice(1);
      if (!id) return;
      const el = document.getElementById(id);
      if (!el) return;
      e.preventDefault();
      const top = el.getBoundingClientRect().top + window.scrollY - (nav?.offsetHeight || 72);
      window.scrollTo({ top, behavior: prefersReduced ? "auto" : "smooth" });
    });
  });

  /* ---------- Hero particles ---------- */
  const canvas = document.getElementById("hero-particles");
  if (canvas && !prefersReduced) {
    const ctx = canvas.getContext("2d");
    let particles = [];
    let w = 0;
    let h = 0;

    function resize() {
      const parent = canvas.parentElement;
      w = parent.clientWidth || window.innerWidth;
      h = parent.clientHeight || window.innerHeight;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const count = Math.round((w * h) / 16000);
      particles = [];
      for (let i = 0; i < Math.max(52, Math.min(count, 110)); i++) {
        particles.push({
          x: Math.random() * w,
          y: Math.random() * h,
          vx: (Math.random() - 0.5) * 0.35,
          vy: (Math.random() - 0.5) * 0.35,
          r: Math.random() * 1.4 + 0.6,
        });
      }
    }

    resize();
    window.addEventListener("resize", resize, { passive: true });

    let rafId;
    function frame() {
      ctx.clearRect(0, 0, w, h);
      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < -20 || p.x > w + 20) p.vx *= -1;
        if (p.y < -20 || p.y > h + 20) p.vy *= -1;
      });

      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const a = particles[i];
          const b = particles[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const maxDist = Math.min(w, h) * 0.095;
          if (dist < maxDist && dist > 0) {
            const alpha = 1 - dist / maxDist;
            ctx.strokeStyle = `rgba(56,189,248,${alpha * 0.38})`;
            ctx.lineWidth = 0.6;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }

      particles.forEach((p) => {
        const gradient = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 3);
        gradient.addColorStop(0, "rgba(52,211,153,0.85)");
        gradient.addColorStop(0.55, "rgba(14,165,233,0.35)");
        gradient.addColorStop(1, "rgba(14,165,233,0)");
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r * 1.35, 0, Math.PI * 2);
        ctx.fill();
      });

      rafId = window.requestAnimationFrame(frame);
    }
    frame();
    window.addEventListener(
      "pagehide",
      () => window.cancelAnimationFrame(rafId),
      { once: true },
    );
  }

  /* ---------- Animated stat counters ---------- */
  const statEls = document.querySelectorAll("[data-counter]");
  let played = false;

  function animateValue(el, end, decimals, durationMs) {
    const startTs = performance.now();

    function fmt(v) {
      if (decimals <= 0) return Math.round(v).toLocaleString("en-IN");
      return Number(v.toFixed(decimals)).toLocaleString("en-IN", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      });
    }

    function tick(now) {
      const p = Math.min(1, (now - startTs) / durationMs);
      const eased = 1 - Math.pow(1 - p, 3);
      const val = eased * end;
      el.textContent = fmt(val);
      if (p < 1) window.requestAnimationFrame(tick);
    }
    window.requestAnimationFrame(tick);
  }

  const ioStats = new IntersectionObserver(
    (entries, obs) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting || played) return;
        played = true;
        statEls.forEach((el) => {
          const target = Number(el.getAttribute("data-target"));
          const dec = Number(el.getAttribute("data-decimals") || "0");
          if (!Number.isFinite(target)) return;
          const ms = prefersReduced ? 50 : Number(el.getAttribute("data-duration") || "1600");
          animateValue(el, target, dec, ms);
        });
        obs.disconnect();
      });
    },
    { threshold: 0.25 },
  );

  const statsRoot = document.getElementById("stats");
  if (statsRoot && statEls.length) ioStats.observe(statsRoot);

  /* ---------- AI pulse bar micro interaction ---------- */
  const pulseFill = document.getElementById("aiPulseFill");
  if (pulseFill && !prefersReduced) {
    window.requestAnimationFrame(() => {
      pulseFill.style.transition = "width 2.9s cubic-bezier(0.16,1,0.3,1)";
      pulseFill.style.width = "76%";
    });
    pulseFill.dataset.state = "b";
    window.setInterval(() => {
      const next = pulseFill.dataset.state === "a" ? "b" : "a";
      pulseFill.dataset.state = next;
      pulseFill.style.transition = "width 2.9s cubic-bezier(0.16,1,0.3,1)";
      pulseFill.style.width = next === "a" ? "86%" : "64%";
    }, 2980);
  }

  /* ---------- AOS ---------- */
  if (window.AOS && !prefersReduced) {
    window.AOS.init({
      duration: 760,
      once: true,
      offset: 48,
      easing: "ease-out-cubic",
    });
  }

  /* ---------- Year in footer ---------- */
  const yr = document.getElementById("year");
  if (yr) yr.textContent = String(new Date().getFullYear());

  window.ArogyaCareLanding = window.ArogyaCareLanding || {};
  window.ArogyaCareLanding.hideLoader = hideLoader;
})();
