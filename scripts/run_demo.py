import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gravity_ras.config import load_config
from gravity_ras.dataio import (
    load_matrices, save_matrix, save_metrics, 
    check_shapes, balance_check
)
from gravity_ras.gravity import gravity_init
from gravity_ras.ras import ras_balance
from gravity_ras.assemble import stack_by_sector
from gravity_ras.validate import calc_discrepancy


def main():
    print("=" * 60)
    print("Gravity-RAS Implementation Demo")
    print("=" * 60)
    
    cfg = load_config("data/config.json")
    print(f"\nConfiguration loaded:")
    print(f"  α={cfg.alpha}, β={cfg.beta}, γ={cfg.gamma}")
    print(f"  max_iter={cfg.max_iter}, tol={cfg.tol}")
    
    print("\nLoading input data...")
    T_row, T_col, L, regions, sectors = load_matrices(
        "data/T_row.csv",
        "data/T_col.csv",
        "data/L.csv"
    )
    
    print(f"  Regions: {regions}")
    print(f"  Sectors: {sectors}")
    print(f"  Matrix shapes: T_row={T_row.shape}, T_col={T_col.shape}, L={L.shape}")
    
    print("\nValidating data consistency...")
    check_shapes(T_row, T_col, L)
    balance = balance_check(T_row, T_col)
    print(f"  Total shipments: {balance['total_shipments']:.1f}")
    print(f"  Total receipts: {balance['total_receipts']:.1f}")
    print(f"  Difference: {balance['difference']:.1f} ({balance['difference_pct']:.2f}%)")
    
    T_hats = {}
    all_metrics = {
        "configuration": {
            "alpha": cfg.alpha,
            "beta": cfg.beta,
            "gamma": cfg.gamma
        },
        "balance_check": balance,
        "sectors": {}
    }
    
    print("\n" + "=" * 60)
    print("Processing sectors...")
    print("=" * 60)
    
    for s_idx, sector in enumerate(sectors):
        print(f"\n[{sector}] Processing...")
        
        Trow_s = T_row[s_idx, :]
        Tcol_s = T_col[s_idx, :]
        
        print(f"  Row totals: {Trow_s}")
        print(f"  Col totals: {Tcol_s}")
        
        print(f"  Applying gravity model...")
        T0 = gravity_init(Trow_s, Tcol_s, L, cfg)
        
        print(f"  Initial gravity allocation:")
        for i, r in enumerate(regions):
            print(f"    {r}: {T0[i, :].round(1)}")
        
        print(f"  Running RAS balancing...")
        T_hat, info = ras_balance(T0, Trow_s, Tcol_s, cfg)
        
        print(f"  Converged: {info['converged']} ({info['iterations']} iterations)")
        print(f"  Max error: {info['max_error']:.2e}")
        
        discrepancy = calc_discrepancy(T_hat, Trow_s, Tcol_s)
        
        print(f"  Final balanced matrix:")
        for i, r in enumerate(regions):
            print(f"    {r}: {T_hat[i, :].round(1)}")
        
        print(f"  Validation:")
        print(f"    Row sums: {T_hat.sum(axis=1).round(1)} (target: {Trow_s})")
        print(f"    Col sums: {T_hat.sum(axis=0).round(1)} (target: {Tcol_s})")
        
        T_hats[sector] = T_hat
        
        save_matrix(
            f"outputs/flows_by_sector/{sector}.csv",
            T_hat,
            regions,
            regions
        )
        
        all_metrics["sectors"][sector] = {
            "convergence": info,
            "discrepancy": discrepancy
        }
    
    print("\n" + "=" * 60)
    print("Creating combined block matrix...")
    print("=" * 60)
    
    T_block, labels = stack_by_sector(T_hats, regions, sectors)
    
    print(f"  Block matrix shape: {T_block.shape}")
    print(f"  Labels: {labels[:3]}...{labels[-3:]}")
    
    save_matrix("outputs/T_block.csv", T_block, labels, labels)
    
    print("\nSaving metrics...")
    save_metrics("outputs/metrics.json", all_metrics)
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"✓ Processed {len(sectors)} sectors")
    print(f"✓ Generated {len(sectors)} flow matrices")
    print(f"✓ Created {T_block.shape[0]}×{T_block.shape[1]} combined block matrix")
    print("\nOutput files:")
    print("  - outputs/flows_by_sector/P1.csv, P2.csv, P3.csv")
    print("  - outputs/T_block.csv")
    print("  - outputs/metrics.json")
    
    print("\n✅ Gravity-RAS computation completed successfully!")


if __name__ == "__main__":
    main()