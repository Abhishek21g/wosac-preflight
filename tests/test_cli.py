from pathlib import Path
from unittest.mock import patch

from wosac_preflight.cli import main

SAMPLE = Path(__file__).resolve().parents[1] / "dashboard" / "sample_receipt.json"


def test_doctor_command_json(capsys):
  code = main(["doctor", str(SAMPLE), "--json"])
  assert code == 0
  out = capsys.readouterr().out
  assert '"metametric": 0.712' in out


def test_doctor_missing_file():
  code = main(["doctor", "/nonexistent/receipt.json"])
  assert code != 0


@patch("wosac_preflight.cli.webbrowser.open")
def test_demo_opens_dashboard(mock_open):
  code = main(["demo"])
  assert code == 0
  mock_open.assert_called_once()
  uri = mock_open.call_args[0][0]
  assert "dashboard/index.html" in uri or "sample_receipt" in uri
