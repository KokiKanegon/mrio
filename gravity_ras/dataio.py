import json
from typing import Tuple, List, Dict, Any
import numpy as np
import pandas as pd


def load_matrices(
    row_path: str, 
    col_path: str, 
    L_path: str
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, List[str], List[str]]:
    
    df_row = pd.read_csv(row_path, index_col=0)
    df_col = pd.read_csv(col_path, index_col=0)
    df_L = pd.read_csv(L_path, index_col=0)
    
    sectors = df_row.index.tolist()
    regions = df_row.columns.tolist()
    
    T_row = df_row.values.astype(float)
    T_col = df_col.values.astype(float)
    L = df_L.values.astype(float)
    
    return T_row, T_col, L, regions, sectors


def save_matrix(
    path: str, 
    matrix: np.ndarray, 
    index_labels: List[str], 
    col_labels: List[str]
) -> None:
    df = pd.DataFrame(matrix, index=index_labels, columns=col_labels)
    df.to_csv(path)


def save_metrics(path: str, metrics: Dict[str, Any]) -> None:
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2, default=str)


def check_shapes(T_row: np.ndarray, T_col: np.ndarray, L: np.ndarray) -> bool:
    n_sectors, n_regions = T_row.shape
    
    if T_col.shape != (n_sectors, n_regions):
        raise ValueError(f"Shape mismatch: T_row {T_row.shape} vs T_col {T_col.shape}")
    
    if L.shape != (n_regions, n_regions):
        raise ValueError(f"Distance matrix shape {L.shape} doesn't match regions {n_regions}")
    
    if not np.allclose(L, L.T):
        print("Warning: Distance matrix is not symmetric")
    
    return True


def balance_check(T_row: np.ndarray, T_col: np.ndarray) -> Dict[str, float]:
    total_row = T_row.sum()
    total_col = T_col.sum()
    diff = total_row - total_col
    diff_pct = (diff / total_row) * 100 if total_row > 0 else 0
    
    return {
        "total_shipments": total_row,
        "total_receipts": total_col,
        "difference": diff,
        "difference_pct": diff_pct,
        "balanced": np.abs(diff_pct) < 0.1
    }