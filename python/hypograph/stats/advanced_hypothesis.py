from typing import Dict, Any, Tuple, List
import numpy as np
from scipy import stats
from ..adapters.base import GraphAdapter

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
