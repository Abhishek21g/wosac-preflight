const BASELINES = {
  logged_oracle: 0.823,
  sumo: 0.653,
  trafficbots: 0.699,
  smart_r1: 0.786,
};

const SMART_R1_BUCKETS = [0.494, 0.811, 0.92];
let radarChart = null;

function fmt(v, d = 3) {
  return v == null ? "—" : Number(v).toFixed(d);
}

function bucketClass(b) {
  if (b === "kinematic") return "tag-kinematic";
  if (b === "interactive") return "tag-interactive";
  return "tag-map_based";
}

function barColor(bucket) {
  if (bucket === "kinematic") return "#9b8cf8";
  if (bucket === "interactive") return "#5b9cf5";
  return "#3dd68c";
}

function renderReceipt(r) {
  document.getElementById("scenarioLabel").textContent = r.scenario_id
    ? `scenario ${r.scenario_id}`
    : "";

  document.getElementById("metametric").textContent = fmt(r.metametric);
  document.getElementById("kin").textContent = fmt(r.kinematic_score);
  document.getElementById("int").textContent = fmt(r.interactive_score);
  document.getElementById("map").textContent = fmt(r.map_based_score);

  const gates = document.getElementById("gateList");
  gates.innerHTML = (r.gates || [])
    .map(
      (g) => `
        <li>
          <span class="${g.passed ? "gate-pass" : "gate-fail"}">${g.passed ? "✓" : "✗"}</span>
          <span><strong>${g.name}</strong><br/><span style="color:var(--muted)">${g.detail}</span></span>
        </li>`
    )
    .join("");

  const feats = [...(r.features || [])].sort(
    (a, b) => (a.likelihood ?? 0) - (b.likelihood ?? 0)
  );

  const tbody = document.querySelector("#featureTable tbody");
  tbody.innerHTML = feats
    .map((f) => {
      const pct = f.likelihood != null ? Math.round(f.likelihood * 100) : 0;
      const weak = f.likelihood != null && f.likelihood < 0.45;
      return `<tr${weak ? ' style="background:#1a1520"' : ""}>
          <td class="name">${f.name.replace(/_/g, " ")}</td>
          <td><span class="tag ${bucketClass(f.bucket)}">${f.bucket}</span></td>
          <td>${fmt(f.likelihood)}</td>
          <td>
            <div style="font-size:0.68rem;color:var(--muted);margin-bottom:2px">w=${f.weight}</div>
            <div class="bar-bg"><div class="bar-fill" style="width:${pct}%;background:${barColor(f.bucket)}"></div></div>
          </td></tr>`;
    })
    .join("");

  const weakest = feats.find((f) => f.likelihood != null);
  const fixEl = document.getElementById("fixFirst");
  if (weakest && r.metametric != null) {
    fixEl.hidden = false;
    fixEl.innerHTML = `Fix first: <strong>${weakest.name.replace(/_/g, " ")}</strong> — likelihood ${fmt(weakest.likelihood)} (weight ${weakest.weight}). ${weakest.name === "traffic_light_violation" ? "New in WOSAC 2025." : ""}`;
  } else {
    fixEl.hidden = true;
  }

  const rateConfig = [
    ["rateCollision", r.simulated_collision_rate, 0.05],
    ["rateOffroad", r.simulated_offroad_rate, 0.03],
    ["rateTl", r.simulated_traffic_light_violation_rate, 0.05],
  ];
  rateConfig.forEach(([id, val, warn]) => {
    const el = document.getElementById(id);
    el.querySelector(".val").textContent = fmt(val, 2);
    el.classList.toggle("high", val != null && val > warn);
    el.classList.toggle("warn", val != null && val > warn * 0.6 && val <= warn);
  });

  const bb = document.getElementById("baselineBody");
  if (r.metametric != null) {
    bb.innerHTML = Object.entries(BASELINES)
      .map(([name, score]) => {
        const d = r.metametric - score;
        const col = d >= 0 ? "var(--good)" : "var(--bad)";
        return `<tr><td class="name">${name}</td><td>${fmt(score)}</td><td style="color:${col}">${d >= 0 ? "+" : ""}${d.toFixed(3)}</td></tr>`;
      })
      .join("");
  } else {
    bb.innerHTML = "";
  }

  document.getElementById("adeLabel").textContent =
    r.average_displacement_error != null
      ? `ADE ${fmt(r.average_displacement_error, 2)} m · minADE ${fmt(r.min_average_displacement_error, 2)} m`
      : "";

  const ctx = document.getElementById("radarChart");
  if (radarChart) radarChart.destroy();
  radarChart = new Chart(ctx, {
    type: "radar",
    data: {
      labels: ["Kinematic", "Interactive", "Map-based"],
      datasets: [
        {
          label: "Your submission",
          data: [r.kinematic_score, r.interactive_score, r.map_based_score].map(
            (v) => v ?? 0
          ),
          borderColor: "#5b9cf5",
          backgroundColor: "rgba(91,156,245,0.18)",
          pointBackgroundColor: "#5b9cf5",
        },
        {
          label: "SMART-R1 (ref)",
          data: SMART_R1_BUCKETS,
          borderColor: "#8b97ad",
          backgroundColor: "rgba(139,151,173,0.05)",
          borderDash: [4, 4],
          pointRadius: 0,
        },
      ],
    },
    options: {
      scales: {
        r: {
          min: 0,
          max: 1,
          ticks: { display: false },
          grid: { color: "#2a3348" },
          angleLines: { color: "#2a3348" },
          pointLabels: { color: "#8b97ad", font: { size: 11 } },
        },
      },
      plugins: { legend: { labels: { color: "#8b97ad", boxWidth: 12 } } },
    },
  });

  window.__lastReceipt = r;
}

async function loadJson(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function initDashboard() {
  document.getElementById("fileInput").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    renderReceipt(JSON.parse(await file.text()));
  });

  document.getElementById("loadSample").addEventListener("click", () => {
    loadJson("sample_receipt.json").then(renderReceipt);
  });

  document.getElementById("copyReceipt")?.addEventListener("click", async () => {
    if (!window.__lastReceipt) return;
    await navigator.clipboard.writeText(JSON.stringify(window.__lastReceipt, null, 2));
    const btn = document.getElementById("copyReceipt");
    const prev = btn.textContent;
    btn.textContent = "Copied!";
    setTimeout(() => { btn.textContent = prev; }, 1500);
  });

  (async () => {
    const params = new URLSearchParams(location.search);
    const receiptParam = params.get("receipt");
    if (receiptParam) {
      try {
        renderReceipt(await loadJson(receiptParam));
        return;
      } catch (_) {
        /* fall through */
      }
    }
    loadJson("sample_receipt.json").then(renderReceipt).catch(() => {});
  })();
}

document.addEventListener("DOMContentLoaded", initDashboard);
