import json
from dataclasses import dataclass
from typing import Optional


@dataclass
class GravityRASConfig:
    alpha: float = 1.0
    beta: float = 1.0
    gamma: float = 2.0
    max_iter: int = 1000
    tol: float = 1e-9
    eps: float = 1e-12
    min_distance: float = 1.0
    intra_region_mode: Optional[str] = None


def load_config(path: str) -> GravityRASConfig:
    with open(path, 'r') as f:
        data = json.load(f)
    return GravityRASConfig(**data)