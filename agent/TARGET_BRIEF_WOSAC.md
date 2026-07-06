# WOSAC Preflight — Target Brief

**Product:** Local official WOSAC 2025 evaluator before 44k-scenario submission  
**Problem canvas:** `../agent/COMPANY_PROBLEM_CANVAS.md`  
**PR (separate):** waymax#93 traffic-light sync

---

## Architecture

```
┌─────────────┐     ┌──────────────────────────────────────┐
│  CLI (host) │────▶│  Docker: tensorflow:2.12 + WOD 1.6.7 │
│  macOS/Linux│     │  score_one.py → official metrics     │
└─────────────┘     └──────────────────────────────────────┘
        │                        │
        ▼                        ▼
  receipt.json            .preflight_out.json
        │
        ▼
  doctor (terminal) + dashboard (Chart.js)
```

**Why Docker:** `waymo-open-dataset` wheels are Linux-only. Host CLI orchestrates; scoring runs in container.

---

## CLI commands

| Command | Purpose | Needs Docker |
|---------|---------|--------------|
| `demo` | Open dashboard with sample/bundled receipt | No |
| `doctor <receipt>` | Terminal summary; `--json` for CI | No |
| `validate` | Format gates only (32 rollouts, agent IDs) | Yes |
| `score` | Full 2025 metametric + feature breakdown | Yes |
| `smoke` | Bundled WOMD test scenario + test submission | Yes |

---

## Receipt schema (`schema_version: 1.0`)

- **Layer 1:** `gates[]` — submission_specs, scenario_id_match
- **Layer 2:** `format_ok`
- **Layer 3:** `metametric`, bucket scores, `features[]` (10 likelihoods), safety rates
- **Meta:** `scenario_id`, `challenge`, `generated_at`, `notes`, `errors`

---

## 2025 metric weights (official)

From `challenge_2025_sim_agents_config.textproto`:

| Bucket | Features | Total weight |
|--------|----------|--------------|
| Kinematic (0.20) | linear_speed, linear_acceleration, angular_speed, angular_acceleration | 0.05 each |
| Interactive (0.45) | distance_to_nearest_object (0.10), collision_indication (0.25), time_to_collision (0.10) | |
| Map-based (0.35) | distance_to_road_edge (0.05), offroad_indication (0.25), **traffic_light_violation (0.05)** | |

---

## Ship checklist

- [ ] 15+ pytest green
- [ ] `wosac-preflight demo` works without Docker
- [ ] `wosac-preflight smoke` green with Docker
- [ ] `github.com/Abhishek21g/wosac-preflight`
- [ ] `enaguthi.com/wosac-preflight/site/`

---

## Not in scope (v0.1)

- Waymax rollout adapter (stretch)
- Scenario Gen challenge mode (separate product option B)
- WOMD Scenario Atlas (option C, deferred)
