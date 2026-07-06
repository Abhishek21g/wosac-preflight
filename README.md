# WOSAC Preflight

Local evaluator for the [Waymo Open Sim Agents Challenge](https://waymo.com/open/challenges/2025/sim-agents/) (WOSAC) 2025 metrics — before you burn a day generating 32 rollouts × 44,926 test scenarios.

## The problem

WOSAC scores submissions with a weighted **metametric** over 10 feature likelihoods (kinematic, interactive, map-based — including **traffic light violation** as of 2025). The leaderboard gives you one number. The official tutorial ends with "this step may take a significant amount of time."

There is no local tool to answer:

- Will my submission pass format validation?
- Which metric bucket is killing my score?
- Is my collision / offroad / TL violation rate sane on a dev shard?

**WOSAC Preflight** runs the **official** `waymo-open-dataset` metric code on one scenario (or smoke test data) and produces a receipt + interactive dashboard.

## Quick start

```bash
pip install -e .
wosac-preflight smoke          # bundled WOMD test scenario (Docker)
wosac-preflight demo           # open dashboard with sample receipt

# Your validation shard + rollouts binproto:
wosac-preflight score \
  --scenario-tfrecord $WOMD/validation/validation.tfrecord-00000-of-00150 \
  --scenario-index 0 \
  --rollouts my_rollouts.binproto \
  --open
```

Requires **Docker** on macOS (waymo-open-dataset wheels are Linux-only).

## Commands

| Command | What it does |
|---------|----------------|
| `smoke` | Official metrics on bundled test scenario + submission |
| `validate` | Format gates only (32 rollouts, 80 steps, agent IDs) |
| `score` | Full 2025 metametric + per-feature breakdown |
| `doctor` | Terminal summary of a receipt JSON |
| `demo` | Open dashboard |

## Dashboard

Load a receipt JSON to see:

- Meta-metric + 3 bucket scores (radar vs SMART-R1 reference)
- Per-feature likelihood bars sorted weakest-first
- Format gate checklist
- Collision / offroad / TL violation rates
- Leaderboard baseline comparison

## Architecture

```
validate → score (official waymo-open-dataset in Docker) → receipt.json → dashboard
```

Metric weights match `challenge_2025_sim_agents_config.textproto` (TL violation = 0.05).

## License note

Scoring uses `waymo_open_dataset.wdl_limited.sim_agents_metrics` (Waymo license + patent terms). See [waymo-open-dataset](https://github.com/waymo-research/waymo-open-dataset).

## Not affiliated with Waymo

Independent tool by [Abhishek Enaguthi](https://enaguthi.com). Complements upstream Waymax/WOMD — not a substitute for the official submission server.
