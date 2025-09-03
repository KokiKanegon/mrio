from typing import Dict, List, Any
import numpy as np
from .config import GravityRASConfig
from .gravity import gravity_init
from .ras import ras_balance


def calc_discrepancy(
    X: np.ndarray,
    row_targets: np.ndarray,
    col_targets: np.ndarray
) -> Dict[str, Any]:
    
    row_sums = X.sum(axis=1)
    col_sums = X.sum(axis=0)
    
    row_diff = row_sums - row_targets
    col_diff = col_sums - col_targets
    
    row_mae = np.abs(row_diff).mean()
    col_mae = np.abs(col_diff).mean()
    
    row_rmse = np.sqrt((row_diff ** 2).mean())
    col_rmse = np.sqrt((col_diff ** 2).mean())
    
    row_max_abs = np.abs(row_diff).max()
    col_max_abs = np.abs(col_diff).max()
    
    row_rel_err = np.abs(row_diff / (row_targets + 1e-10)).mean() * 100
    col_rel_err = np.abs(col_diff / (col_targets + 1e-10)).mean() * 100
    
    return {
        "row_mae": float(row_mae),
        "col_mae": float(col_mae),
        "row_rmse": float(row_rmse),
        "col_rmse": float(col_rmse),
        "row_max_abs": float(row_max_abs),
        "col_max_abs": float(col_max_abs),
        "row_relative_error_pct": float(row_rel_err),
        "col_relative_error_pct": float(col_rel_err),
        "total_mae": float((row_mae + col_mae) / 2),
        "total_rmse": float((row_rmse + col_rmse) / 2)
    }


def sensitivity_gamma(
    T_row: np.ndarray,
    T_col: np.ndarray,
    L: np.ndarray,
    gammas: List[float],
    cfg: GravityRASConfig
) -> List[Dict[str, Any]]:
    
    results = []
    
    for gamma_val in gammas:
        cfg_temp = GravityRASConfig(
            alpha=cfg.alpha,
            beta=cfg.beta,
            gamma=gamma_val,
            max_iter=cfg.max_iter,
            tol=cfg.tol,
            eps=cfg.eps,
            min_distance=cfg.min_distance
        )
        
        T0 = gravity_init(T_row, T_col, L, cfg_temp)
        X, info = ras_balance(T0, T_row, T_col, cfg_temp)
        
        n_regions = L.shape[0]
        avg_distance = 0
        total_flow = 0
        
        for i in range(n_regions):
            for j in range(n_regions):
                if i != j:
                    flow = X[i, j]
                    avg_distance += flow * L[i, j]
                    total_flow += flow
        
        if total_flow > 0:
            avg_distance /= total_flow
        
        intra_share = np.diag(X).sum() / X.sum() * 100
        
        results.append({
            "gamma": gamma_val,
            "iterations": info["iterations"],
            "converged": info["converged"],
            "avg_distance": float(avg_distance),
            "intra_regional_share": float(intra_share),
            "total_flow": float(X.sum())
        })
    
    return results