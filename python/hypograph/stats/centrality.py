from typing import Dict, Any, List
from ..adapters.base import GraphAdapter

def degree_centrality(adapter: GraphAdapter, direction: str = "BOTH", node_filter: str = None, edge_filter: str = None) -> Dict[str, float]:
    """
    Calculate degree centrality for each node.
    Normalized by N-1.
    """
    # Get total nodes for normalization (filtered)
    node_where = f"WHERE {node_filter}" if node_filter else ""
    count_res = adapter.query(f"MATCH (n) {node_where} RETURN count(n) as count")
    n_nodes = count_res[0]['count']
    
    if n_nodes <= 1:
        return {}
        
    # Query degrees
    # Filters:
    # Node filter applies to 'n'.
    # Edge filter applies to 'r'.
    # Neighbor filter (induced subgraph) applies to neighbor.
    
    edge_conditions = []
    if node_filter:
        # Neighbor must also satisfy filter
        # Note: In degree centrality, we usually count edges to ANY node in the graph?
        # Or only to nodes in the subgraph?
        # "Induced subgraph" implies only edges within the subgraph.
        # So neighbor must satisfy node_filter.
        # Direction matters for neighbor variable.
        pass # Logic handled below
        
    # Construct query based on direction
    if direction == "IN":
        # MATCH (n)<-[r]-(m)
        neighbor = "m"
        pattern = f"(n)<-[r]-({neighbor})"
    elif direction == "OUT":
        # MATCH (n)-[r]->(m)
        neighbor = "m"
        pattern = f"(n)-[r]->({neighbor})"
    else:
        # MATCH (n)-[r]-(m)
        neighbor = "m"
        pattern = f"(n)-[r]-({neighbor})"
        
    where_clauses = []
    if node_filter:
        where_clauses.append(f"({node_filter})") # n
        where_clauses.append(f"({node_filter.replace('n', neighbor)})") # neighbor
    if edge_filter:
        where_clauses.append(f"({edge_filter})")
        
    full_where = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    query = f"MATCH {pattern} {full_where} RETURN id(n) as id, count(r) as degree"
        
    results = adapter.query(query)
    
    centrality = {}
    for row in results:
        # Normalize
        centrality[str(row['id'])] = row['degree'] / (n_nodes - 1)
        
    return centrality

def pagerank(adapter: GraphAdapter, damping: float = 0.85, iterations: int = 20, node_filter: str = None, edge_filter: str = None) -> Dict[str, float]:
    """
    Calculate PageRank.
    """
    # GDS PageRank with filters requires Cypher projection
    try:
        node_query = f"MATCH (n) WHERE {node_filter} RETURN id(n) as id" if node_filter else "MATCH (n) RETURN id(n) as id"
        
        edge_conditions = []
        if node_filter:
            m_filter = node_filter.replace("n", "m")
            edge_conditions.append(f"({node_filter})")
            edge_conditions.append(f"({m_filter})")
        if edge_filter:
            edge_conditions.append(f"({edge_filter})")
        edge_where = "WHERE " + " AND ".join(edge_conditions) if edge_conditions else ""
        
        edge_query = f"MATCH (n)-[r]->(m) {edge_where} RETURN id(n) as source, id(m) as target"

        query = f"""
        CALL gds.pageRank.stream({{
            nodeQuery: "{node_query}",
            relationshipQuery: "{edge_query}",
            dampingFactor: {damping},
            maxIterations: {iterations}
        }})
        YIELD nodeId, score
        RETURN nodeId, score
        """
        results = adapter.query(query)
        return {str(row['nodeId']): row['score'] for row in results}
    except Exception:
        print("Native PageRank not available. Returning degree centrality as fallback.")
        return degree_centrality(adapter, node_filter=node_filter, edge_filter=edge_filter)

def betweenness_centrality(adapter: GraphAdapter, node_filter: str = None, edge_filter: str = None) -> Dict[str, float]:
    """
    Calculate Betweenness Centrality.
    """
    try:
        node_query = f"MATCH (n) WHERE {node_filter} RETURN id(n) as id" if node_filter else "MATCH (n) RETURN id(n) as id"
        
        edge_conditions = []
        if node_filter:
            m_filter = node_filter.replace("n", "m")
            edge_conditions.append(f"({node_filter})")
            edge_conditions.append(f"({m_filter})")
        if edge_filter:
            edge_conditions.append(f"({edge_filter})")
        edge_where = "WHERE " + " AND ".join(edge_conditions) if edge_conditions else ""
        
        edge_query = f"MATCH (n)-[r]->(m) {edge_where} RETURN id(n) as source, id(m) as target"

        query = f"""
        CALL gds.betweenness.stream({{
            nodeQuery: "{node_query}",
            relationshipQuery: "{edge_query}"
        }})
        YIELD nodeId, score
        RETURN nodeId, score
        """
        results = adapter.query(query)
        return {str(row['nodeId']): row['score'] for row in results}
    except Exception:
        print("Native Betweenness not available.")
        return {}
