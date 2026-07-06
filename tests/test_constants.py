from wosac_preflight.constants import BUCKETS, FEATURE_WEIGHTS, N_ROLLOUTS, N_SIMULATION_STEPS


def test_feature_weights_sum_to_one():
  assert abs(sum(FEATURE_WEIGHTS.values()) - 1.0) < 1e-9


def test_all_features_in_buckets():
  bucketed = {n for names in BUCKETS.values() for n in names}
  assert set(FEATURE_WEIGHTS) == bucketed


def test_bucket_count():
  assert len(BUCKETS) == 3
  assert len(FEATURE_WEIGHTS) == 10


def test_wosac_rollout_requirements():
  assert N_ROLLOUTS == 32
  assert N_SIMULATION_STEPS == 80


def test_traffic_light_violation_in_map_bucket():
  assert "traffic_light_violation" in BUCKETS["map_based"]
  assert FEATURE_WEIGHTS["traffic_light_violation"] == 0.05


def test_collision_is_heaviest_feature():
  assert FEATURE_WEIGHTS["collision_indication"] == max(FEATURE_WEIGHTS.values())
