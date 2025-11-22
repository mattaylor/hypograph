from typing import Dict, Any
from ..adapters.base import GraphAdapter

def calculate_density(adapter: GraphAdapter, weight_property: str = None, node_filter: str = None, edge_filter: str = None) -> float:
    """
    Calculate the density of the graph.
    If weight_property is provided, calculates weighted density (sum of weights / potential edges).
    Density = 2 * |E| / (|V| * (|V| - 1)) for undirected graphs.
    
    Args:
        node_filter: Cypher WHERE clause for nodes (e.g., "n.age > 20")
        edge_filter: Cypher WHERE clause for edges (e.g., "r.weight > 0.5")
    """
    # Node count
    node_where = f"WHERE {node_filter}" if node_filter else ""
    node_count_res = adapter.query(f"MATCH (n) {node_where} RETURN count(n) as count")
    
    # Edge count (Induced Subgraph)
    # If node_filter is present, we must ensure both endpoints satisfy it.
    where_clauses = []
    if node_filter:
        where_clauses.append(f"({node_filter})") # Source n
        # For the target node 'm', we need to replace 'n' with 'm' in the filter string or use a generic approach.
        # Simple string replacement is risky. A better approach for 'n' is to alias correctly.
        # Let's assume the user provides a filter string that uses 'n' for the node.
        # We will map it to 'm' by replacing 'n.' with 'm.' and 'n ' with 'm '.
        # This is a bit hacky but standard for simple string injection.
        # Alternatively, we just use the same filter if it doesn't reference the variable name (unlikely).
        # A safer way: "MATCH (n)-[r]->(m) WHERE ..."
        # We can inject the filter for 'n' and a modified filter for 'm'.
        # For MVP, let's assume the filter is simple and we can just apply it to 'n' and 'm'.
        # Actually, let's just use the filter string as is for 'n', and try to adapt for 'm'.
        # Or simpler: require the user to write filters that don't depend on the variable name? No, that's impossible in Cypher.
        # Let's assume the user writes "n.prop > x". We need to apply "m.prop > x".
        # We will do a simple replace of "n" with "m" for the target node filter.
        m_filter = node_filter.replace("n", "m")
        where_clauses.append(f"({m_filter})")
        
    if edge_filter:
        where_clauses.append(f"({edge_filter})")
        
    edge_where = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    if weight_property:
        edge_query = f"MATCH (n)-[r]->(m) {edge_where} RETURN sum(r.{weight_property}) as count"
    else:
        edge_query = f"MATCH (n)-[r]->(m) {edge_where} RETURN count(r) as count"
        
    edge_count_res = adapter.query(edge_query)
    
    node_count = node_count_res[0]['count']
    edge_val = edge_count_res[0]['count'] or 0 # Handle None if no edges
    
    if node_count < 2:
        return 0.0
        
    return (2 * edge_val) / (node_count * (node_count - 1))

def get_degree_distribution(adapter: GraphAdapter, weight_property: str = None, node_filter: str = None, edge_filter: str = None) -> Dict[float, int]:
    """
    Get the degree distribution of the graph.
    If weight_property is provided, calculates weighted degree (strength).
    Returns a dictionary mapping degree/strength to count of nodes with that value.
    """
    node_where = f"WHERE {node_filter}" if node_filter else ""
    
    # For edges, we need to filter the neighbors and the relationship
    edge_conditions = []
    if node_filter:
        # We need to filter the neighbor 'm'
        m_filter = node_filter.replace("n", "m")
        edge_conditions.append(f"({m_filter})")
    if edge_filter:
        edge_conditions.append(f"({edge_filter})")
        
    edge_where = "WHERE " + " AND ".join(edge_conditions) if edge_conditions else ""
    
    if weight_property:
        # We use a subquery or pattern comprehension to handle the optional match with filters correctly
        # But generic Cypher might be older. Let's stick to standard OPTIONAL MATCH with WHERE.
        query = f"""
        MATCH (n) {node_where}
        OPTIONAL MATCH (n)-[r]-(m)
        {edge_where}
        WITH n, sum(coalesce(r.{weight_property}, 0)) as degree
        RETURN degree, count(n) as count
        ORDER BY degree
        """
    else:
        query = f"""
        MATCH (n) {node_where}
        OPTIONAL MATCH (n)-[r]-(m)
        {edge_where}
        WITH n, count(r) as degree
        RETURN degree, count(n) as count
        ORDER BY degree
        """
    results = adapter.query(query)
    return {row['degree']: row['count'] for row in results}
