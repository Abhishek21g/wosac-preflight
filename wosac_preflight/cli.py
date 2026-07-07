"""WOSAC Preflight CLI — validate and score before leaderboard submission."""

from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from pathlib import Path

from wosac_preflight import docker_runner
from wosac_preflight.doctor import receipt_from_payload, render_doctor
from wosac_preflight.receipt import PreflightReceipt

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "dashboard" / "index.html"
SAMPLE_RECEIPT = ROOT / "dashboard" / "sample_receipt.json"


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
      prog="wosac-preflight",
      description=(
          "Local WOSAC evaluator — official 2025 metrics before a 44k-scenario submission."
      ),
  )
  sub = parser.add_subparsers(dest="command", required=True)

  smoke_p = sub.add_parser("smoke", help="Run bundled WOMD test scenario (Docker)")
  smoke_p.add_argument("-o", "--output", type=Path, default=Path("receipts/smoke.json"))
  smoke_p.add_argument(
      "--from-ci",
      action="store_true",
      help="Download latest official smoke receipt from GitHub Actions (no Docker)",
  )
  smoke_p.set_defaults(handler=_cmd_smoke)

  val_p = sub.add_parser("validate", help="Format gate only (32 rollouts, agent IDs)")
  val_p.add_argument("--scenario-tfrecord", type=Path, required=True)
  val_p.add_argument("--scenario-index", type=int, default=0)
  val_p.add_argument("--rollouts", type=Path, required=True)
  val_p.add_argument("-o", "--output", type=Path, default=None)
  val_p.set_defaults(handler=_cmd_validate)

  score_p = sub.add_parser("score", help="Full official metametric for one scenario")
  score_p.add_argument("--scenario-tfrecord", type=Path, required=True)
  score_p.add_argument("--scenario-index", type=int, default=0)
  score_p.add_argument("--rollouts", type=Path, required=True)
  score_p.add_argument("-o", "--output", type=Path, default=Path("receipts/score.json"))
  score_p.add_argument("--open", action="store_true", help="Open dashboard after scoring")
  score_p.set_defaults(handler=_cmd_score)

  doc_p = sub.add_parser("doctor", help="Summarize a receipt JSON")
  doc_p.add_argument("receipt", type=Path)
  doc_p.add_argument("--json", action="store_true")
  doc_p.set_defaults(handler=_cmd_doctor)

  demo_p = sub.add_parser("demo", help="Open dashboard with sample or given receipt")
  demo_p.add_argument("--receipt", type=Path, default=None)
  demo_p.set_defaults(handler=_cmd_demo)

  args = parser.parse_args(argv)
  try:
    return args.handler(args)
  except RuntimeError as exc:
    print(f"error: {exc}", file=sys.stderr)
    return 1


def _cmd_smoke(args) -> int:
  args.output.parent.mkdir(parents=True, exist_ok=True)
  if args.from_ci:
    print("Fetching official smoke receipt from GitHub Actions...")
    data = docker_runner.fetch_ci_smoke(args.output)
  else:
    print("Running Docker smoke test (official WOSAC metrics)...")
    data = docker_runner.run_mode("smoke", output=args.output)
  receipt = receipt_from_payload(data)
  print(render_doctor(receipt))
  print(f"\nWrote {args.output}")
  return 0


def _cmd_validate(args) -> int:
  data = docker_runner.run_mode(
      "validate",
      scenario_tfrecord=args.scenario_tfrecord,
      scenario_index=args.scenario_index,
      rollouts=args.rollouts,
      output=args.output,
  )
  print(json.dumps(data, indent=2))
  return 0 if data.get("format_ok") else 1


def _cmd_score(args) -> int:
  print("Scoring with official 2025 WOSAC metrics (Docker)...")
  args.output.parent.mkdir(parents=True, exist_ok=True)
  data = docker_runner.run_mode(
      "score",
      scenario_tfrecord=args.scenario_tfrecord,
      scenario_index=args.scenario_index,
      rollouts=args.rollouts,
      output=args.output,
  )
  receipt = receipt_from_payload(data)
  print(render_doctor(receipt))
  print(f"\nWrote {args.output}")
  if args.open:
    _open_dashboard(args.output)
  return 0 if receipt.format_ok and receipt.metametric is not None else 1


def _cmd_doctor(args) -> int:
  if not args.receipt.exists():
    print(f"error: receipt not found: {args.receipt}", file=sys.stderr)
    return 1
  receipt = PreflightReceipt.load(args.receipt)
  if args.json:
    print(json.dumps(receipt.to_dict(), indent=2))
  else:
    print(render_doctor(receipt))
  return 0


def _cmd_demo(args) -> int:
  path = args.receipt or SAMPLE_RECEIPT
  if not path.exists():
    print(f"Missing receipt {path}. Run: wosac-preflight smoke", file=sys.stderr)
    return 1
  _open_dashboard(path)
  return 0


def _open_dashboard(receipt_path: Path) -> None:
  uri = DASHBOARD.resolve().as_uri() + f"?receipt={receipt_path.resolve().as_uri()}"
  print(f"Opening dashboard: {uri}")
  webbrowser.open(uri)


if __name__ == "__main__":
  raise SystemExit(main())
