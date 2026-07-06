from wosac_preflight.doctor import receipt_from_payload, render_doctor
from wosac_preflight.receipt import FeatureScore, GateResult, PreflightReceipt


def test_receipt_from_minimal_validate_payload():
  data = {
      "scenario_id": "abc123",
      "gates": [{"name": "submission_specs", "passed": False, "detail": "bad rollouts"}],
      "format_ok": False,
  }
  receipt = receipt_from_payload(data)
  assert not receipt.format_ok
  assert receipt.metametric is None
  assert len(receipt.gates) == 1


def test_doctor_shows_fail_gate():
  receipt = PreflightReceipt(
      scenario_id="x",
      gates=[GateResult("submission_specs", False, "missing agents")],
      format_ok=False,
      errors=["Format validation failed"],
  )
  text = render_doctor(receipt)
  assert "[FAIL]" in text
  assert "missing agents" in text


def test_doctor_skips_scores_when_format_fails():
  receipt = PreflightReceipt(scenario_id="x", format_ok=False)
  text = render_doctor(receipt)
  assert "metametric" not in text


def test_doctor_shows_weakest_features():
  features = [
      FeatureScore("collision_indication", 0.9, 0.25, "interactive"),
      FeatureScore("traffic_light_violation", 0.2, 0.05, "map_based"),
  ]
  receipt = PreflightReceipt(
      scenario_id="x",
      format_ok=True,
      metametric=0.7,
      kinematic_score=0.5,
      interactive_score=0.8,
      map_based_score=0.6,
      features=features,
      simulated_collision_rate=0.01,
      simulated_offroad_rate=0.02,
      simulated_traffic_light_violation_rate=0.1,
  )
  text = render_doctor(receipt)
  assert "traffic_light_violation" in text
  assert "likelihood=0.200" in text


def test_receipt_roundtrip_dict():
  receipt = PreflightReceipt(
      scenario_id="abc",
      format_ok=True,
      metametric=0.75,
      gates=[GateResult("submission_specs", True, "ok")],
      features=[FeatureScore("linear_speed", 0.6, 0.05, "kinematic")],
  )
  restored = PreflightReceipt.load_from_dict(receipt.to_dict())
  assert restored.scenario_id == "abc"
  assert restored.metametric == 0.75
  assert restored.gates[0].passed
