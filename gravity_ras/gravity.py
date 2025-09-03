from typing import Tuple, Optional, Dict
import numpy as np
from .config import GravityRASConfig


def sanitize_distance(L: np.ndarray, cfg: GravityRASConfig) -> np.ndarray:
    L_safe = L.copy()
    L_safe[L_safe < cfg.min_distance] = cfg.min_distance
    return L_safe


def apply_intra_region_rule(
    T0: np.ndarray,
    Trow: np.ndarray,
    Tcol: np.ndarray,
    intra_mode: Optional[str],
    intra_ratio: float = 0.5
) -> Dict[str, np.ndarray]:
    
    n_regions = T0.shape[0]
    T0_intra = np.zeros_like(T0)
    T0_residual = T0.copy()
    
    if intra_mode == "fixed_ratio":
        for r in range(n_regions):
            intra_val = min(Trow[r], Tcol[r]) * intra_ratio
            T0_intra[r, r] = intra_val
            T0_residual[r, r] = 0
    
    return {
        "intra": T0_intra,
        "residual": T0_residual,
        "total": T0_intra + T0_residual
    }


def gravity_init(
    Trow: np.ndarray,
    Tcol: np.ndarray,
    L: np.ndarray,
    cfg: GravityRASConfig
) -> np.ndarray:
    
    L_safe = sanitize_distance(L, cfg)
    
    n_regions = len(Trow)
    G = np.zeros((n_regions, n_regions))
    
    for i in range(n_regions):
        for j in range(n_regions):
            G[i, j] = (
                (Trow[i] ** cfg.alpha) * 
                (Tcol[j] ** cfg.beta) / 
                (L_safe[i, j] ** cfg.gamma)
            )
    
    row_sums = G.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    t_ratio = G / row_sums
    
    T0 = t_ratio * Trow[:, np.newaxis]
    
    return T0


def gravity_with_intra(
    Trow: np.ndarray,
    Tcol: np.ndarray,
    L: np.ndarray,
    cfg: GravityRASConfig,
    intra_ratio: float = 0.5
) -> Tuple[np.ndarray, np.ndarray]:
    
    T0_base = gravity_init(Trow, Tcol, L, cfg)
    
    if cfg.intra_region_mode:
        result = apply_intra_region_rule(
            T0_base, Trow, Tcol, cfg.intra_region_mode, intra_ratio
        )
        return result["total"], result["residual"]
    else:
        return T0_base, np.zeros_like(T0_base)