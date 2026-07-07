import json
from pathlib import Path

from wosac_preflight.doctor import receipt_from_payload, render_doctor
from wosac_preflight.receipt import PreflightReceipt

SAMPLE = Path(__file__).resolve().parents[1] / "dashboard" / "sample_receipt.json"


def test_sample_receipt_loads():
  data = json.loads(SAMPLE.read_text())
  receipt = receipt_from_payload(data)
  assert receipt.format_ok
  assert receipt.metametric is not None
  assert 0.0 <= receipt.metametric <= 1.0
  assert len(receipt.features) == 10


def test_weakest_features():
  receipt = PreflightReceipt.load(SAMPLE)
  weak = receipt.weakest_features(1)
  assert weak[0].likelihood is not None
  assert weak[0].likelihood < 0.5


def test_doctor_renders():
  receipt = PreflightReceipt.load(SAMPLE)
  text = render_doctor(receipt)
  assert "metametric" in text
  assert "637f20cafde22ff8" in text
