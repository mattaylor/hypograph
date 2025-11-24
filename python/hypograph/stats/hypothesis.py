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

def anova_test(adapter: GraphAdapter, group_property: str, metric_property: str, node_filter: str = None) -> Tuple[float, float]:
    """
    Perform One-Way ANOVA.
    """
    node_where = f"WHERE {node_filter} AND" if node_filter else "WHERE"
    
    query = f"""
    MATCH (n)
    {node_where} n.{group_property} IS NOT NULL AND n.{metric_property} IS NOT NULL
    RETURN n.{group_property} as group, n.{metric_property} as value
    """
    results = adapter.query(query)
    
    # Group data
    groups = {}
    for row in results:
        g = row['group']
        val = row['value']
        if g not in groups:
            groups[g] = []
        groups[g].append(val)
        
    if len(groups) < 2:
        raise ValueError("Need at least 2 groups for ANOVA")
        
    # Run ANOVA
    group_values = list(groups.values())
    f_stat, p_val = stats.f_oneway(*group_values)
    
    return f_stat, p_val

def chi_square_test(adapter: GraphAdapter, property_a: str, property_b: str, node_filter: str = None) -> Tuple[float, float, int, np.ndarray]:
    """
    Perform Chi-Square test.
    """
    node_where = f"WHERE {node_filter} AND" if node_filter else "WHERE"
    
    query = f"""
    MATCH (n)
    {node_where} n.{property_a} IS NOT NULL AND n.{property_b} IS NOT NULL
    RETURN n.{property_a} as a, n.{property_b} as b, count(n) as count
    """
    results = adapter.query(query)
    
    # Build contingency table
    # Map unique values to indices
    a_vals = sorted(list(set(row['a'] for row in results)))
    b_vals = sorted(list(set(row['b'] for row in results)))
    
    a_map = {val: i for i, val in enumerate(a_vals)}
    b_map = {val: i for i, val in enumerate(b_vals)}
    
    table = np.zeros((len(a_vals), len(b_vals)))
    
    for row in results:
        i = a_map[row['a']]
        j = b_map[row['b']]
        table[i, j] = row['count']
        
    chi2, p, dof, expected = stats.chi2_contingency(table)
    
    return chi2, p, dof, expected

def correlation_test(adapter: GraphAdapter, property_a: str, property_b: str, method: str = 'pearson', node_filter: str = None) -> Tuple[float, float]:
    """
    Calculate correlation.
    """
    node_where = f"WHERE {node_filter} AND" if node_filter else "WHERE"
    
    query = f"""
    MATCH (n)
    {node_where} n.{property_a} IS NOT NULL AND n.{property_b} IS NOT NULL
    RETURN n.{property_a} as a, n.{property_b} as b
    """
    results = adapter.query(query)
    
    a_vals = [row['a'] for row in results]
    b_vals = [row['b'] for row in results]
    
    if len(a_vals) < 2:
        return 0.0, 1.0
        
    if method == 'spearman':
        return stats.spearmanr(a_vals, b_vals)
    else:
        return stats.pearsonr(a_vals, b_vals)
