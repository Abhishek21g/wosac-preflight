"""Turn Docker JSON payload into PreflightReceipt + terminal report."""

from __future__ import annotations

from wosac_preflight.constants import BASELINE_METAMETRIC, BUCKETS, FEATURE_WEIGHTS
from wosac_preflight.receipt import FeatureScore, GateResult, PreflightReceipt


def receipt_from_payload(data: dict) -> PreflightReceipt:
  gates = [GateResult(**g) for g in data.get("gates", [])]
  features = [FeatureScore(**f) for f in data.get("features", [])]
  if not features and data.get("metametric") is not None:
    features = _features_from_weights_only()

  return PreflightReceipt(
      scenario_id=data.get("scenario_id", ""),
      gates=gates,
      format_ok=bool(data.get("format_ok", False)),
      metametric=data.get("metametric"),
      kinematic_score=data.get("kinematic_score"),
      interactive_score=data.get("interactive_score"),
      map_based_score=data.get("map_based_score"),
      features=features,
      average_displacement_error=data.get("average_displacement_error"),
      min_average_displacement_error=data.get("min_average_displacement_error"),
      simulated_collision_rate=data.get("simulated_collision_rate"),
      simulated_offroad_rate=data.get("simulated_offroad_rate"),
      simulated_traffic_light_violation_rate=data.get(
          "simulated_traffic_light_violation_rate"
      ),
      evaluated_agent_ids=data.get("evaluated_agent_ids", []),
      simulated_agent_ids=data.get("simulated_agent_ids", []),
      notes=data.get("notes", []),
      errors=data.get("errors", []),
  )


def _features_from_weights_only() -> list[FeatureScore]:
  bucket_for = {n: b for b, names in BUCKETS.items() for n in names}
  return [
      FeatureScore(name=n, likelihood=None, weight=w, bucket=bucket_for[n])
      for n, w in FEATURE_WEIGHTS.items()
  ]


def render_doctor(receipt: PreflightReceipt) -> str:
  lines = [
      f"WOSAC Preflight — {receipt.scenario_id or '(smoke)'}",
      "=" * 60,
      "",
      "## Gates",
  ]
  for g in receipt.gates:
    mark = "PASS" if g.passed else "FAIL"
    lines.append(f"  [{mark}] {g.name}: {g.detail}")

  if receipt.metametric is not None and receipt.kinematic_score is not None:
    lines += [
        "",
        "## Scores (official 2025 metametric)",
        f"  metametric:  {receipt.metametric:.4f}",
        f"  kinematic:   {receipt.kinematic_score:.4f}",
        f"  interactive: {receipt.interactive_score:.4f}",
        f"  map_based:   {receipt.map_based_score:.4f}",
        "",
        "## vs published baselines",
    ]
    for name, score in BASELINE_METAMETRIC.items():
      delta = receipt.metametric - score
      lines.append(f"  {name:14} {score:.3f}  (Δ {delta:+.3f})")

    lines += ["", "## Weakest features (fix these first)"]
    for f in receipt.weakest_features(3):
      if f.likelihood is not None:
        lines.append(f"  {f.name:30} likelihood={f.likelihood:.3f}  weight={f.weight}")

    lines += [
        "",
        "## Safety rates (simulated)",
    ]
    if receipt.simulated_collision_rate is not None:
      lines.append(f"  collision:     {receipt.simulated_collision_rate:.4f}")
    if receipt.simulated_offroad_rate is not None:
      lines.append(f"  offroad:       {receipt.simulated_offroad_rate:.4f}")
    if receipt.simulated_traffic_light_violation_rate is not None:
      lines.append(f"  TL violation:  {receipt.simulated_traffic_light_violation_rate:.4f}")

  if receipt.errors:
    lines += ["", "## Errors", *[f"  - {e}" for e in receipt.errors]]

  return "\n".join(lines)
