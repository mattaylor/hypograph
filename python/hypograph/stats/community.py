from typing import List, Dict, Any
from ..adapters.base import GraphAdapter

def detect_communities_label_propagation(adapter: GraphAdapter, write_property: str = "community", weight_property: str = None, node_filter: str = None, edge_filter: str = None):
    """
    Run Label Propagation.
    Note: GDS projection with filters is complex. We will use a Cypher projection if possible.
    """
    # Construct Cypher projection
    node_query = f"MATCH (n) WHERE {node_filter} RETURN id(n) as id" if node_filter else "MATCH (n) RETURN id(n) as id"
    
    edge_conditions = []
    if node_filter:
        m_filter = node_filter.replace("n", "m")
        edge_conditions.append(f"({node_filter})") # Source
        edge_conditions.append(f"({m_filter})")    # Target
    if edge_filter:
        edge_conditions.append(f"({edge_filter})")
        
    edge_where = "WHERE " + " AND ".join(edge_conditions) if edge_conditions else ""
    
    if weight_property:
        edge_query = f"MATCH (n)-[r]->(m) {edge_where} RETURN id(n) as source, id(m) as target, r.{weight_property} as weight"
        relationship_weight_property = "weight"
    else:
        edge_query = f"MATCH (n)-[r]->(m) {edge_where} RETURN id(n) as source, id(m) as target"
        relationship_weight_property = None

    query = f"""
    CALL gds.labelPropagation.write({{
        nodeQuery: "{node_query}",
        relationshipQuery: "{edge_query}",
        writeProperty: "{write_property}"
        {f', relationshipWeightProperty: "{relationship_weight_property}"' if relationship_weight_property else ''}
    }})
    YIELD nodeCount, communityCount, ranIterations, didConverge
    RETURN nodeCount, communityCount, ranIterations, didConverge
    """
    return adapter.query(query)

def get_modularity(adapter: GraphAdapter, community_property: str = "community", weight_property: str = None, node_filter: str = None, edge_filter: str = None) -> float:
    """
    Calculate modularity.
    """
    # We need to sum weights/counts within communities vs total.
    # Modularity Q = (1/2m) * sum( (A_ij - k_i*k_j/2m) * delta(c_i, c_j) )
    
    # 1. Total weight (2m)
    # 2. For each community, sum of internal weights and sum of degrees.
    
    # Filters
    node_where = f"WHERE {node_filter}" if node_filter else ""
    
    edge_conditions = []
    if node_filter:
        m_filter = node_filter.replace("n", "m")
        edge_conditions.append(f"({m_filter})")
    if edge_filter:
        edge_conditions.append(f"({edge_filter})")
    edge_where = "WHERE " + " AND ".join(edge_conditions) if edge_conditions else ""
    
    # Total weight (m)
    if weight_property:
        m_query = f"MATCH (n)-[r]->(m) {node_where} {('AND ' + edge_where[6:]) if edge_where else ''} RETURN sum(r.{weight_property}) as m"
    else:
        m_query = f"MATCH (n)-[r]->(m) {node_where} {('AND ' + edge_where[6:]) if edge_where else ''} RETURN count(r) as m"
        
    m_res = adapter.query(m_query)
    m = m_res[0]['m'] or 0
    
    if m == 0:
        return 0.0
        
    # We can compute Q by iterating over communities?
    # Or a single big query?
    # Q = sum( (ls/m) - (ds/2m)^2 )
    # ls = sum of weights inside community c
    # ds = sum of degrees of nodes in community c
    
    # Query for ls and ds per community
    if weight_property:
        # ls: internal edges
        # ds: total degree of nodes in community (including edges to outside)
        # Note: ds calculation needs to respect the subgraph filters!
        
        # This is getting complex for a single query.
        # Let's simplify:
        # MATCH (n) WHERE filters
        # OPTIONAL MATCH (n)-[r]-(m) WHERE filters (induced subgraph)
        # WITH n, community, sum(weight) as k_i
        # RETURN community, sum(k_i) as ds, ... wait, ls is harder.
        pass
        
    # Simplified approach:
    # 1. Get communities and their nodes
    # 2. Calculate ls and ds for each community
    
    # Actually, let's try a single query approach
    
    w_expr = f"r.{weight_property}" if weight_property else "1"
    
    query = f"""
    MATCH (n) {node_where}
    WHERE n.{community_property} IS NOT NULL
    WITH n, n.{community_property} as comm
    
    // Calculate degree k_i in the induced subgraph
    OPTIONAL MATCH (n)-[r]-(m)
    WHERE {node_filter.replace('n', 'm') if node_filter else 'true'} 
    AND {edge_filter if edge_filter else 'true'}
    WITH n, comm, sum({w_expr}) as k_i
    
    // Aggregate per community
    WITH comm, sum(k_i) as ds, collect(n) as nodes
    
    // Calculate internal edges ls (sum of weights of edges where both ends are in comm)
    // This is expensive to do with collect(n).
    // Better:
    // MATCH (n)-[r]->(m) WHERE n.comm = m.comm AND filters
    """
    
    # Let's stick to the definition: Q = sum_c ( e_cc - a_c^2 )
    # e_cc = fraction of edges within community c
    # a_c = fraction of edge ends in community c
    
    # Total weight M (sum of all weights) = m (if undirected, total weight is m, 2m in formula usually refers to degree sum = 2 * weight sum)
    # Let's use M = sum of weights.
    
    M = m # Total edge weight
    
    # Calculate e_cc and a_c for each community
    # e_cc query:
    # MATCH (n)-[r]->(m) WHERE n.comm = m.comm AND filters RETURN n.comm, sum(w)
    
    e_cc_query = f"""
    MATCH (n)-[r]->(m)
    {node_where}
    AND n.{community_property} = m.{community_property}
    AND {node_filter.replace('n', 'm') if node_filter else 'true'}
    AND {edge_filter if edge_filter else 'true'}
    RETURN n.{community_property} as comm, sum({w_expr}) as weight
    """
    
    # a_c query:
    # MATCH (n) WHERE filters
    # OPTIONAL MATCH (n)-[r]-(m) WHERE filters
    # RETURN n.comm, sum(w)
    
    a_c_query = f"""
    MATCH (n) {node_where}
    OPTIONAL MATCH (n)-[r]-(m)
    WHERE {node_filter.replace('n', 'm') if node_filter else 'true'}
    AND {edge_filter if edge_filter else 'true'}
    RETURN n.{community_property} as comm, sum({w_expr}) as degree
    """
    
    e_cc_res = adapter.query(e_cc_query)
    a_c_res = adapter.query(a_c_query)
    
    e_cc_map = {row['comm']: row['weight'] for row in e_cc_res}
    a_c_map = {row['comm']: row['degree'] for row in a_c_res}
    
    communities = set(e_cc_map.keys()) | set(a_c_map.keys())
    
    modularity = 0.0
    for comm in communities:
        e = (e_cc_map.get(comm, 0) or 0) / M
        a = (a_c_map.get(comm, 0) or 0) / (2 * M)
        modularity += e - a**2
        
    return modularityal_weight
