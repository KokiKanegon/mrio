from typing import List, Tuple, Dict
import numpy as np


def stack_by_sector(
    T_hats: Dict[str, np.ndarray],
    regions: List[str],
    sectors: List[str]
) -> Tuple[np.ndarray, List[str]]:
    
    n_regions = len(regions)
    n_sectors = len(sectors)
    total_size = n_regions * n_sectors
    
    T_block = np.zeros((total_size, total_size))
    
    labels = []
    for region in regions:
        for sector in sectors:
            labels.append(f"{region}-{sector}")
    
    for s_idx, sector in enumerate(sectors):
        T_hat = T_hats[sector]
        
        for i in range(n_regions):
            for j in range(n_regions):
                block_i = i * n_sectors + s_idx
                block_j = j * n_sectors + s_idx
                T_block[block_i, block_j] = T_hat[i, j]
    
    return T_block, labels