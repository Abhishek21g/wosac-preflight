import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from wosac_preflight import docker_runner


def test_docker_available_false_when_missing(monkeypatch):
  monkeypatch.setattr("shutil.which", lambda _: None)
  assert not docker_runner.docker_available()


def test_ensure_image_raises_without_docker(monkeypatch):
  monkeypatch.setattr(docker_runner, "docker_available", lambda: False)
  with pytest.raises(RuntimeError, match="Docker is required"):
    docker_runner.ensure_image()


def test_mount_file_returns_container_path(tmp_path):
  f = tmp_path / "scenario.tfrecord"
  f.write_bytes(b"data")
  cpath, mounts = docker_runner._mount_file(f, "scenario")
  assert cpath.endswith("/scenario.tfrecord")
  assert len(mounts) == 2
  assert str(tmp_path) in mounts[1]


@patch("wosac_preflight.docker_runner.ensure_image")
@patch("wosac_preflight.docker_runner.subprocess.run")
def test_run_mode_smoke_parses_output(mock_run, mock_ensure, tmp_path):
  payload = {"scenario_id": "smoke", "format_ok": True, "metametric": 0.8}
  out = docker_runner.ROOT / ".preflight_out.json"
  out.write_text(json.dumps(payload))
  mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

  result = docker_runner.run_mode("smoke", output=tmp_path / "receipt.json")
  assert result["metametric"] == 0.8
  assert (tmp_path / "receipt.json").exists()
  out.unlink(missing_ok=True)


@patch("wosac_preflight.docker_runner.ensure_image")
def test_run_mode_validate_requires_paths(mock_ensure):
  with pytest.raises(ValueError, match="required"):
    docker_runner.run_mode("score")
