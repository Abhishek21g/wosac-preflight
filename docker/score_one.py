#!/usr/bin/env python3
# Official WOSAC eval — runs inside Linux Docker image with waymo-open-dataset.
"""Score or validate one WOSAC scenario using official Waymo metrics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import tensorflow as tf
from google.protobuf import text_format
from waymo_open_dataset.protos import scenario_pb2
from waymo_open_dataset.protos import sim_agents_metrics_pb2
from waymo_open_dataset.protos import sim_agents_submission_pb2
from waymo_open_dataset.utils.sim_agents import submission_specs
from waymo_open_dataset.wdl_limited.sim_agents_metrics import metrics

CHALLENGE = submission_specs.ChallengeType.SIM_AGENTS


def _load_metrics_config() -> sim_agents_metrics_pb2.SimAgentMetricsConfig:
  path = _vendor_dir() / "challenge_2025_sim_agents_config.textproto"
  config = sim_agents_metrics_pb2.SimAgentMetricsConfig()
  text_format.Parse(path.read_text(encoding="utf-8"), config)
  return config


def _vendor_dir() -> Path:
  here = Path(__file__).resolve().parent
  for candidate in (here / "vendor" / "testdata", here.parent / "vendor" / "testdata"):
    if candidate.exists():
      return candidate
  raise FileNotFoundError("vendor/testdata not found (expected bundled smoke fixtures)")


def _load_scenario(path: str, index: int) -> scenario_pb2.Scenario:
  if path.endswith(".tfrecord") or "tfrecord" in Path(path).name:
    ds = tf.data.TFRecordDataset([path])
    for i, raw in enumerate(ds.as_numpy_iterator()):
      if i == index:
        return scenario_pb2.Scenario.FromString(raw)
    raise IndexError(f"scenario index {index} out of range in {path}")
  # Bundled smoke scenario from vendor testdata
  vendor = _vendor_dir()
  scenario_path = vendor / "motion_data_one_scenario.tfrecord"
  if not scenario_path.exists():
    raise FileNotFoundError(f"Missing bundled scenario: {scenario_path}")
  return _load_scenario(str(scenario_path), 0)


def _load_rollouts(path: str, scenario_id: str | None) -> sim_agents_submission_pb2.ScenarioRollouts:
  data = Path(path).read_bytes()
  # Try full submission first
  try:
    submission = sim_agents_submission_pb2.SimAgentsChallengeSubmission.FromString(data)
    if submission.scenario_rollouts:
      rollouts = submission.scenario_rollouts[0]
      if scenario_id and rollouts.scenario_id != scenario_id:
        for r in submission.scenario_rollouts:
          if r.scenario_id == scenario_id:
            return r
      return rollouts
  except Exception:
    pass
  rollouts = sim_agents_submission_pb2.ScenarioRollouts.FromString(data)
  return rollouts


def _gates_from_validation(scenario, rollouts) -> list[dict]:
  gates = []
  try:
    submission_specs.validate_scenario_rollouts(rollouts, scenario, CHALLENGE)
    gates.append({"name": "submission_specs", "passed": True, "detail": "32 rollouts, 80 steps, agent IDs OK"})
  except ValueError as exc:
    gates.append({"name": "submission_specs", "passed": False, "detail": str(exc)})
  sid_ok = rollouts.scenario_id == scenario.scenario_id
  gates.append({
      "name": "scenario_id_match",
      "passed": sid_ok,
      "detail": f"rollouts={rollouts.scenario_id!r} scenario={scenario.scenario_id!r}",
  })
  return gates


def _feature_scores(scenario_metrics) -> list[dict]:
  weights = {
      "linear_speed": 0.05,
      "linear_acceleration": 0.05,
      "angular_speed": 0.05,
      "angular_acceleration": 0.05,
      "distance_to_nearest_object": 0.10,
      "collision_indication": 0.25,
      "time_to_collision": 0.10,
      "distance_to_road_edge": 0.05,
      "offroad_indication": 0.25,
      "traffic_light_violation": 0.05,
  }
  bucket_for = {
      "linear_speed": "kinematic",
      "linear_acceleration": "kinematic",
      "angular_speed": "kinematic",
      "angular_acceleration": "kinematic",
      "distance_to_nearest_object": "interactive",
      "collision_indication": "interactive",
      "time_to_collision": "interactive",
      "distance_to_road_edge": "map_based",
      "offroad_indication": "map_based",
      "traffic_light_violation": "map_based",
  }
  out = []
  for name, weight in weights.items():
    field = f"{name}_likelihood"
    likelihood = getattr(scenario_metrics, field, None)
    out.append({
        "name": name,
        "likelihood": float(likelihood),
        "weight": weight,
        "bucket": bucket_for[name],
    })
  return out


def run_validate(scenario, rollouts) -> dict:
  gates = _gates_from_validation(scenario, rollouts)
  sim_ids = list(submission_specs.get_sim_agent_ids(scenario, CHALLENGE))
  eval_ids = list(submission_specs.get_evaluation_sim_agent_ids(scenario, CHALLENGE))
  format_ok = all(g["passed"] for g in gates)
  return {
      "scenario_id": scenario.scenario_id,
      "gates": gates,
      "format_ok": format_ok,
      "simulated_agent_ids": sim_ids,
      "evaluated_agent_ids": eval_ids,
  }


def run_score(scenario, rollouts) -> dict:
  base = run_validate(scenario, rollouts)
  base["format_ok"] = all(g["passed"] for g in base["gates"])
  if not base["format_ok"]:
    base["errors"] = ["Format validation failed; skipping official metrics."]
    return base

  config = _load_metrics_config()
  scenario_metrics = metrics.compute_scenario_metrics_for_bundle(
      config, scenario, rollouts, CHALLENGE
  )
  bucketed = metrics.aggregate_metrics_to_buckets(config, scenario_metrics)

  base.update({
      "metametric": float(scenario_metrics.metametric),
      "kinematic_score": float(bucketed.kinematic_metrics),
      "interactive_score": float(bucketed.interactive_metrics),
      "map_based_score": float(bucketed.map_based_metrics),
      "features": _feature_scores(scenario_metrics),
      "average_displacement_error": float(scenario_metrics.average_displacement_error),
      "min_average_displacement_error": float(scenario_metrics.min_average_displacement_error),
      "simulated_collision_rate": float(scenario_metrics.simulated_collision_rate),
      "simulated_offroad_rate": float(scenario_metrics.simulated_offroad_rate),
      "simulated_traffic_light_violation_rate": float(
          scenario_metrics.simulated_traffic_light_violation_rate
      ),
  })
  return base


def run_smoke() -> dict:
  vendor = _vendor_dir()
  scenario = _load_scenario(str(vendor / "motion_data_one_scenario.tfrecord"), 0)
  rollouts = _load_rollouts(str(vendor / "test_submission.binproto"), scenario.scenario_id)
  result = run_score(scenario, rollouts)
  result["notes"] = ["Bundled WOMD scenario + linear-extrapolation submission from vendor/testdata."]
  return result


def main() -> int:
  parser = argparse.ArgumentParser()
  parser.add_argument("--mode", choices=["validate", "score", "smoke"], default="score")
  parser.add_argument("--scenario-tfrecord", default="")
  parser.add_argument("--scenario-index", type=int, default=0)
  parser.add_argument("--rollouts", default="")
  parser.add_argument("--output", default="-")
  args = parser.parse_args()

  if args.mode == "smoke":
    payload = run_smoke()
  else:
    if not args.scenario_tfrecord or not args.rollouts:
      print("scenario-tfrecord and rollouts required", file=sys.stderr)
      return 2
    scenario = _load_scenario(args.scenario_tfrecord, args.scenario_index)
    rollouts = _load_rollouts(args.rollouts, scenario.scenario_id)
    if args.mode == "validate":
      payload = run_validate(scenario, rollouts)
    else:
      payload = run_score(scenario, rollouts)

  text = json.dumps(payload, indent=2)
  if args.output == "-":
    print(text)
  else:
    Path(args.output).write_text(text, encoding="utf-8")
  return 0 if payload.get("format_ok", payload.get("metametric") is not None) else 1


if __name__ == "__main__":
  sys.exit(main())
