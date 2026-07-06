"""WOSAC 2025 metric weights and bucket groupings (from official config)."""

from __future__ import annotations

# challenge_2025_sim_agents_config.textproto — metametric weights sum to 1.0
FEATURE_WEIGHTS: dict[str, float] = {
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

BUCKETS: dict[str, list[str]] = {
    "kinematic": [
        "linear_speed",
        "linear_acceleration",
        "angular_speed",
        "angular_acceleration",
    ],
    "interactive": [
        "distance_to_nearest_object",
        "collision_indication",
        "time_to_collision",
    ],
    "map_based": [
        "distance_to_road_edge",
        "offroad_indication",
        "traffic_light_violation",
    ],
}

N_ROLLOUTS = 32
N_SIMULATION_STEPS = 80
CURRENT_TIME_INDEX = 10

# Published WOSAC 2025 leaderboard references (approximate, for comparison UI)
BASELINE_METAMETRIC = {
    "logged_oracle": 0.823,
    "sumo": 0.653,
    "trafficbots": 0.699,
    "smart_r1": 0.786,
}
