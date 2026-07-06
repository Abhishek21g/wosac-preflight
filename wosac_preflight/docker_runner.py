"""Run official WOSAC eval inside Docker (Linux-only waymo-open-dataset wheels)."""

from __future__ import annotations

import json
import shutil
import subprocess
import uuid
from pathlib import Path

IMAGE_NAME = "wosac-preflight:latest"
ROOT = Path(__file__).resolve().parents[1]


def docker_available() -> bool:
  return shutil.which("docker") is not None


def ensure_image() -> None:
  if not docker_available():
    raise RuntimeError("Docker is required for official WOSAC scoring on macOS.")
  inspect = subprocess.run(
      ["docker", "image", "inspect", IMAGE_NAME],
      capture_output=True,
  )
  if inspect.returncode != 0:
    subprocess.run(
        [
            "docker", "build", "-t", IMAGE_NAME,
            "-f", str(ROOT / "docker/Dockerfile"),
            str(ROOT),
        ],
        check=True,
    )


def _mount_file(host_path: Path, container_dir: str) -> tuple[str, list[str]]:
  """Return container path and extra -v flags for a host file."""
  host_path = host_path.resolve()
  vol_id = uuid.uuid4().hex[:8]
  cdir = f"/mnt/{vol_id}"
  return f"{cdir}/{host_path.name}", ["-v", f"{host_path.parent}:{cdir}:ro"]


def run_mode(
    mode: str,
    *,
    scenario_tfrecord: Path | None = None,
    scenario_index: int = 0,
    rollouts: Path | None = None,
    output: Path | None = None,
) -> dict:
  ensure_image()
  mounts: list[str] = ["-v", f"{ROOT}:/workspace"]
  cmd = ["docker", "run", "--rm", *mounts, IMAGE_NAME, "--mode", mode]

  if mode != "smoke":
    if scenario_tfrecord is None or rollouts is None:
      raise ValueError("scenario-tfrecord and rollouts required")
    scen_c, m1 = _mount_file(scenario_tfrecord, "scenario")
    roll_c, m2 = _mount_file(rollouts, "rollouts")
    cmd = ["docker", "run", "--rm", *mounts, *m1, *m2, IMAGE_NAME, "--mode", mode]
    cmd += ["--scenario-tfrecord", scen_c]
    cmd += ["--scenario-index", str(scenario_index)]
    cmd += ["--rollouts", roll_c]

  out_path = ROOT / ".preflight_out.json"
  cmd += ["--output", "/workspace/.preflight_out.json"]

  proc = subprocess.run(cmd, capture_output=True, text=True)
  if proc.returncode != 0 and not out_path.exists():
    raise RuntimeError(
        f"Docker scoring failed (exit {proc.returncode}):\n{proc.stderr or proc.stdout}"
    )

  data = json.loads(out_path.read_text(encoding="utf-8"))
  if output:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2), encoding="utf-8")
  return data
