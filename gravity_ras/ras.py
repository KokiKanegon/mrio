from typing import Tuple, Dict, Any
import numpy as np
from .config import GravityRASConfig


def ras_balance(
    T0: np.ndarray,
    row_targets: np.ndarray,
    col_targets: np.ndarray,
    cfg: GravityRASConfig
) -> Tuple[np.ndarray, Dict[str, Any]]:
    
    X = T0.copy()
    X = np.maximum(X, 0)
    
    converged = False
    iteration = 0
    
    for iteration in range(cfg.max_iter):
        row_sums = X.sum(axis=1)
        row_sums[row_sums == 0] = cfg.eps
        r = row_targets / row_sums
        X = r[:, np.newaxis] * X
        
        col_sums = X.sum(axis=0)
        col_sums[col_sums == 0] = cfg.eps
        c = col_targets / col_sums
        X = X * c[np.newaxis, :]
        
        row_error = np.abs(X.sum(axis=1) - row_targets).max()
        col_error = np.abs(X.sum(axis=0) - col_targets).max()
        max_error = max(row_error, col_error)
        
        if max_error < cfg.tol:
            converged = True
            break
    
    info = {
        "iterations": iteration + 1,
        "converged": converged,
        "max_error": float(max_error),
        "row_error": float(row_error),
        "col_error": float(col_error)
    }
    
    return X, info