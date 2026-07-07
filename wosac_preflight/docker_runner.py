"""Run official WOSAC eval inside Docker (Linux-only waymo-open-dataset wheels)."""

from __future__ import annotations

import json
import shlex
import shutil
import subprocess
import uuid
from pathlib import Path

BASE_IMAGE = "python:3.10-bookworm"
ROOT = Path(__file__).resolve().parents[1]

_INSTALL_DEPS = (
    "pip install -q "
    "tensorflow==2.13.0 tensorflow_probability==0.21.0 numpy==1.23.5 "
    "pandas==1.5.3 scikit-learn==1.2.2 absl-py==1.4.0 immutabledict==2.2.0 "
    "'protobuf>=3.20,<5' && "
    "pip install -q --no-deps waymo-open-dataset-tf-2-12-0==1.6.7"
)


def docker_available() -> bool:
  return shutil.which("docker") is not None


def _mount_file(host_path: Path, container_dir: str) -> tuple[str, list[str]]:
  """Return container path and extra -v flags for a host file."""
  host_path = host_path.resolve()
  vol_id = uuid.uuid4().hex[:8]
  cdir = f"/mnt/{vol_id}"
  return f"{cdir}/{host_path.name}", ["-v", f"{host_path.parent}:{cdir}:ro"]


def _run_container(score_argv: list[str], extra_mounts: list[str] | None = None) -> None:
  if not docker_available():
    raise RuntimeError(
        "Docker is required for official WOSAC scoring on macOS.\n"
        "Or run on GitHub Actions: gh workflow run smoke --repo Abhishek21g/wosac-preflight"
    )

  score_cmd = " ".join(shlex.quote(arg) for arg in score_argv)
  inner = f"{_INSTALL_DEPS} && python /workspace/docker/score_one.py {score_cmd}"
  cmd = [
      "docker",
      "run",
      "--rm",
      "-v",
      f"{ROOT}:/workspace",
      "-w",
      "/workspace",
      *(extra_mounts or []),
      BASE_IMAGE,
      "bash",
      "-lc",
      inner,
  ]
  proc = subprocess.run(cmd, capture_output=True, text=True)
  out_path = ROOT / ".preflight_out.json"
  if proc.returncode != 0 and not out_path.exists():
    raise RuntimeError(
        f"Docker scoring failed (exit {proc.returncode}):\n{proc.stderr or proc.stdout}"
    )


def run_mode(
    mode: str,
    *,
    scenario_tfrecord: Path | None = None,
    scenario_index: int = 0,
    rollouts: Path | None = None,
    output: Path | None = None,
) -> dict:
  score_argv = ["--mode", mode, "--output", "/workspace/.preflight_out.json"]
  extra_mounts: list[str] = []

  if mode != "smoke":
    if scenario_tfrecord is None or rollouts is None:
      raise ValueError("scenario-tfrecord and rollouts required")
    scen_c, m1 = _mount_file(scenario_tfrecord, "scenario")
    roll_c, m2 = _mount_file(rollouts, "rollouts")
    extra_mounts = [*m1, *m2]
    score_argv += [
        "--scenario-tfrecord",
        scen_c,
        "--scenario-index",
        str(scenario_index),
        "--rollouts",
        roll_c,
    ]

  _run_container(score_argv, extra_mounts)

  data = json.loads((ROOT / ".preflight_out.json").read_text(encoding="utf-8"))
  if output:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2), encoding="utf-8")
  return data


def fetch_ci_smoke(output: Path) -> dict:
  """Download the latest green smoke receipt from GitHub Actions."""
  if not shutil.which("gh"):
    raise RuntimeError("gh CLI required for --from-ci. Install: brew install gh")

  def _latest_run_id() -> str:
    proc = subprocess.run(
        [
            "gh", "run", "list", "--repo", "Abhishek21g/wosac-preflight",
            "--workflow", "smoke.yml", "--limit", "1",
            "--json", "databaseId,conclusion", "-q", ".[0]",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    import json as _json
    row = _json.loads(proc.stdout)
    if row.get("conclusion") != "success":
      subprocess.run(
          ["gh", "workflow", "run", "smoke.yml", "--repo", "Abhishek21g/wosac-preflight"],
          check=True,
      )
      subprocess.run(
          [
              "gh", "run", "watch",
              subprocess.check_output(
                  [
                      "gh", "run", "list", "--repo", "Abhishek21g/wosac-preflight",
                      "--workflow", "smoke.yml", "--limit", "1", "--json", "databaseId",
                      "-q", ".[0].databaseId",
                  ],
                  text=True,
              ).strip(),
              "--exit-status",
          ],
          check=True,
      )
      return _latest_run_id()
    return str(row["databaseId"])

  run_id = _latest_run_id()
  tmp = ROOT / ".ci_smoke_dl"
  if tmp.exists():
    shutil.rmtree(tmp)
  tmp.mkdir()
  subprocess.run(
      [
          "gh", "run", "download", run_id,
          "--repo", "Abhishek21g/wosac-preflight",
          "-n", "smoke-receipt", "-D", str(tmp),
      ],
      check=True,
  )
  data = json.loads((tmp / "smoke.json").read_text(encoding="utf-8"))
  shutil.rmtree(tmp)
  if output:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2), encoding="utf-8")
  return data
