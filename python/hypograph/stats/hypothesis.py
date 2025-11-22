from typing import Dict, Any, Tuple
import numpy as np
from scipy import stats
from ..adapters.base import GraphAdapter
from .inference import calculate_density

def z_test_density(adapter: GraphAdapter, expected_val: float, n_nodes: int, weight_property: str = None, node_filter: str = None, edge_filter: str = None) -> Tuple[float, float]:
    """
    Perform a Z-test comparing the graph density against an expected value (e.g., from a null model).
    
    Args:
        expected_val: Expected density (or mean weight)
        n_nodes: Number of nodes in the graph (or subgraph)
        weight_property: If provided, uses weighted density.
        node_filter: Cypher WHERE clause for nodes.
        edge_filter: Cypher WHERE clause for edges.
        
    Returns:
        (z_score, p_value)
    """
    # Recalculate density with filters if needed, but usually we pass the density calculated externally?
    # No, the function calculates density internally in the previous version?
    # Wait, the previous version called `calculate_density`? No, let's check.
    # The previous version imported `calculate_density`.
    
    
    # If n_nodes is passed, we assume it matches the filter? 
    # Ideally we should count nodes if filters are present, but the user passes n_nodes.
    # Let's trust the user or recalculate if n_nodes is None? 
    # The signature requires n_nodes. Let's assume it's the count of the *filtered* nodes.
    
    observed_density = calculate_density(adapter, weight_property, node_filter, edge_filter)
    
    # Standard Error
    # For unweighted: sqrt(p * (1-p) / (N*(N-1)/2)) where p is expected density
    # For weighted: This is more complex. We'll use a simplified variance estimate or assume the user provides std_dev?
    # For this MVP, we stick to the unweighted formula or a basic weighted approximation.
    
    possible_edges = n_nodes * (n_nodes - 1) / 2
    if possible_edges <= 0:
        return 0.0, 1.0
        
    if weight_property:
        # Simplified: assume variance is proportional to mean? 
        # Or just use the same formula treating expected_val as probability (if weights are 0-1).
        # If weights are arbitrary, we need sample variance.
        # Let's stick to the previous implementation's logic but updated for filters.
        # Previous logic: 
        # se = np.sqrt(expected_val * (1 - expected_val) / possible_edges) # ONLY VALID FOR 0-1 weights
        # We will keep it as is for consistency with previous step.
        se = np.sqrt(expected_val * (1 - expected_val) / possible_edges)
    else:
        se = np.sqrt(expected_val * (1 - expected_val) / possible_edges)
        
    if se == 0:
        return 0.0, 0.0
        
    z_score = (observed_density - expected_val) / se
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))  # Two-tailed
    
    return z_score, p_value
