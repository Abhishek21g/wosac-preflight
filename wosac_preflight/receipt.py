"""Preflight receipt schema — JSON artifact from validate/score runs."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class GateResult:
  name: str
  passed: bool
  detail: str


@dataclass
class FeatureScore:
  name: str
  likelihood: float | None
  weight: float
  bucket: str


@dataclass
class PreflightReceipt:
  """Full preflight report for one scenario."""

  schema_version: str = "1.0"
  generated_at: str = field(
      default_factory=lambda: datetime.now(timezone.utc).isoformat()
  )
  scenario_id: str = ""
  challenge: str = "sim_agents_2025"

  # Layer 1–2: format gates
  gates: list[GateResult] = field(default_factory=list)
  format_ok: bool = False

  # Layer 3: official scores (None if score not run)
  metametric: float | None = None
  kinematic_score: float | None = None
  interactive_score: float | None = None
  map_based_score: float | None = None

  features: list[FeatureScore] = field(default_factory=list)

  average_displacement_error: float | None = None
  min_average_displacement_error: float | None = None
  simulated_collision_rate: float | None = None
  simulated_offroad_rate: float | None = None
  simulated_traffic_light_violation_rate: float | None = None

  evaluated_agent_ids: list[int] = field(default_factory=list)
  simulated_agent_ids: list[int] = field(default_factory=list)

  notes: list[str] = field(default_factory=list)
  errors: list[str] = field(default_factory=list)

  def to_dict(self) -> dict[str, Any]:
    d = asdict(self)
    d["gates"] = [asdict(g) for g in self.gates]
    d["features"] = [asdict(f) for f in self.features]
    return d

  def save(self, path: Path) -> None:
    path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

  @classmethod
  def load(cls, path: Path) -> PreflightReceipt:
    data = json.loads(path.read_text(encoding="utf-8"))
    return cls.load_from_dict(data)

  @classmethod
  def load_from_dict(cls, data: dict) -> PreflightReceipt:
    data = dict(data)
    gates = [GateResult(**g) for g in data.pop("gates", [])]
    features = [FeatureScore(**f) for f in data.pop("features", [])]
    return cls(gates=gates, features=features, **data)

  def weakest_features(self, n: int = 3) -> list[FeatureScore]:
    scored = [f for f in self.features if f.likelihood is not None]
    return sorted(scored, key=lambda f: f.likelihood)[:n]
