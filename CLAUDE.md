# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gravity-RAS implementation for estimating small-scale regional input-output tables with 3 regions (A, B, C) and 3 sectors (P1=primary, P2=secondary, P3=tertiary).

## Implementation Architecture

### Core Algorithm Flow
1. **Input Data Loading**: Read shipment totals (T_row), receipt totals (T_col), and distance matrix (L)
2. **Gravity Model Initialization**: Calculate initial inter-regional flows using gravity formula
3. **RAS Balancing (IPFP)**: Iteratively adjust flows to match row and column sum constraints
4. **Output Assembly**: Generate sector-specific 3×3 matrices and combined 9×9 region-sector block matrix

### Project Structure

```
gravity_ras/
├── __init__.py
├── config.py       # GravityRASConfig class with all parameters
├── dataio.py       # Data I/O and validation functions
├── gravity.py      # Gravity model initialization
├── ras.py          # RAS/IPFP balancing algorithm  
├── assemble.py     # Matrix assembly functions
└── validate.py     # Validation and sensitivity analysis

scripts/
└── run_demo.py     # Main execution script

data/
├── T_row.csv       # Shipment totals (sectors × regions)
├── T_col.csv       # Receipt totals (sectors × regions)
├── L.csv           # Distance matrix (regions × regions)
└── config.json     # Algorithm parameters

outputs/
├── flows_by_sector/
│   ├── P1.csv      # Primary sector flows
│   ├── P2.csv      # Secondary sector flows
│   └── P3.csv      # Tertiary sector flows
├── T_block.csv     # 9×9 combined matrix
└── metrics.json    # Convergence metrics
```

## Key Functions and Their Specifications

### config.py
```python
class GravityRASConfig:
    alpha: float = 1.0
    beta: float = 1.0
    gamma: float = 2.0
    max_iter: int = 1000
    tol: float = 1e-9
    eps: float = 1e-12
    min_distance: float = 1.0
    intra_region_mode: Optional[str] = None

load_config(path: str) -> GravityRASConfig
```

### dataio.py
```python
load_matrices(row_path, col_path, L_path) -> (T_row, T_col, L, regions, sectors)
save_matrix(path, matrix, index_labels, col_labels)
save_metrics(path, metrics)
check_shapes(T_row, T_col, L) -> bool
balance_check(T_row, T_col) -> dict
```

### gravity.py
```python
sanitize_distance(L, cfg) -> np.ndarray  # Apply min_distance threshold
apply_intra_region_rule(...) -> dict     # Handle diagonal elements
gravity_init(Trow, Tcol, L, cfg) -> np.ndarray  # Main gravity calculation
gravity_with_intra(...) -> (T0_total, T0_residual)  # With intra-region handling
```

**Gravity Formula:**
```
G_i[R,S] = (T_i^{R·})^α × (T_i^{·S})^β / (L^{RS})^γ
t_i^{RS} = G_i[R,S] / Σ_S G_i[R,S]  # Normalize to proportions
T^(0)_i[R,S] = t_i^{RS} × T_i^{R·}  # Apply to row totals
```

### ras.py
```python
def ras_balance(T0, row_targets, col_targets, cfg) -> (X, info):
    X = T0.copy()
    for k in range(max_iter):
        r = row_targets / (X.sum(axis=1) + eps)
        X = r[:, None] * X
        c = col_targets / (X.sum(axis=0) + eps)
        X = X * c[None, :]
        if convergence_check() < tol:
            break
    return X, {"iterations": k, "converged": True/False}
```

### assemble.py
```python
stack_by_sector(T_hats, regions, sectors) -> (T_block, labels)
# Creates 9×9 block matrix with region-sector combinations
```

### validate.py
```python
calc_discrepancy(X, row_targets, col_targets) -> dict
sensitivity_gamma(T_row, T_col, L, gammas, cfg) -> list[dict]
```

### scripts/run_demo.py
Main execution flow:
1. Load configuration from `data/config.json`
2. Load matrices from CSV files
3. Validate data consistency
4. For each sector:
   - Apply gravity model initialization
   - Run RAS balancing
   - Save sector-specific results
5. Assemble 9×9 block matrix
6. Save all outputs and metrics

## Data Specifications

### Input CSV Format Examples

**data/T_row.csv** (Shipment totals by sector and region):
```csv
sector,A,B,C
P1,120,80,100
P2,200,160,140
P3,180,150,170
```

**data/T_col.csv** (Receipt totals by sector and region):
```csv
sector,A,B,C
P1,110,90,100
P2,210,140,150
P3,170,160,170
```

**data/L.csv** (Distance matrix, symmetric with positive diagonal):
```csv
,A,B,C
A,1.0,30,60
B,30,1.0,40
C,60,40,1.0
```

**data/config.json**:
```json
{
  "alpha": 1.0,
  "beta": 1.0,
  "gamma": 2.0,
  "max_iter": 1000,
  "tol": 1e-9,
  "eps": 1e-12,
  "min_distance": 1.0,
  "intra_region_mode": null
}
```

## Development Commands

```bash
# Setup project structure
mkdir -p gravity_ras scripts data outputs/flows_by_sector

# Install dependencies
pip install numpy pandas

# Run the main calculation
python scripts/run_demo.py

# Run with custom config
python scripts/run_demo.py --config path/to/config.json
```

## Validation Requirements

### Mandatory Checks
- **Row sum consistency**: `X.sum(axis=1) ≈ T_row[sector, :]` (within tolerance)
- **Column sum consistency**: `X.sum(axis=0) ≈ T_col[sector, :]` (within tolerance)
- **Non-negativity**: All flow values ≥ 0
- **Shape consistency**: T_row and T_col must be (n_sectors × n_regions)

### Expected Output Example (P1 sector)
```csv
,A,B,C
A,55.2,40.1,24.7
B,29.8,31.6,18.6
C,25.0,18.3,56.7
```
Row sums: [120, 80, 100] ✓
Column sums: [110, 90, 100] ✓

## Implementation Notes

- **Distance handling**: Diagonal elements (intra-regional) use L[r,r]=1.0 by default
- **Numerical stability**: Use eps=1e-12 to avoid division by zero
- **Convergence**: Monitor both row and column discrepancies
- **Performance**: Vectorized NumPy operations throughout

## Current Scope and Limitations

- **Fixed to 3×3**: Designed for 3 regions and 3 sectors
- **No external regions**: ROW (Rest of World) not included
- **Parameters not estimated**: α, β, γ are user-specified, not data-driven
- **Partial I-O implementation**: Focus on flow estimation, not full input-output analysis