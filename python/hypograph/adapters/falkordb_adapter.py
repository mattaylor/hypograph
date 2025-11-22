from typing import Any, Dict, List, Optional
from falkordb import FalkorDB
from .base import GraphAdapter

class FalkorDBAdapter(GraphAdapter):
    """
    Adapter for FalkorDB using the native falkordb client.
    """

    def __init__(self):
        self.client = None
        self.graph = None

    def connect(self, uri: str = "localhost", port: int = 6379, graph_name: str = "hypograph"):
        # Note: FalkorDB client connection might differ slightly based on version, 
        # assuming standard Redis-like connection params or URI.
        # The python client usually takes host/port.
        # URI parsing might be needed if full URI is passed.
        # For simplicity, we'll assume uri is host for now or handle parsing.
        
        # Simple parsing for host:port
        host = uri
        if ":" in uri:
            parts = uri.split(":")
            host = parts[0]
            if len(parts) > 1:
                try:
                    port = int(parts[1])
                except ValueError:
                    pass

        self.client = FalkorDB(host=host, port=port)
        self.graph = self.client.select_graph(graph_name)

    def close(self):
        # FalkorDB client (redis-py based) might not need explicit close, 
        # but good practice to have the method.
        if self.client:
            self.client.close()

    def query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not self.graph:
            raise ConnectionError("Not connected to a graph.")
        
        result = self.graph.query(query, params or {})
        # FalkorDB result set might need processing to match list of dicts format
        # Assuming result.result_set is iterable of records
        
        # Map result to list of dicts. 
        # Note: falkordb-py results structure needs to be handled.
        # Usually it returns a ResultSet object.
        
        output = []
        for record in result.result_set:
            # This depends on how falkordb returns data. 
            # If it returns generic objects, we might need to convert them.
            # For now, assuming we can extract data or it behaves like a list of values.
            # If the query returns nodes/edges, we need to extract properties.
            
            # Simple heuristic: if it's a list of headers and values
            row_data = {}
            if hasattr(result, 'header'):
                for i, header in enumerate(result.header):
                    val = record[i]
                    # If val is a Node or Edge object, extract properties
                    if hasattr(val, 'properties'):
                        row_data[header[0]] = val.properties
                    else:
                        row_data[header[0]] = val
            output.append(row_data)
            
        return output

    def get_nodes(self, label: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "MATCH (n) RETURN n"
        if label:
            query = f"MATCH (n:{label}) RETURN n"
        return self.query(query)

    def get_edges(self, relationship_type: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "MATCH ()-[r]->() RETURN r"
        if relationship_type:
            query = f"MATCH ()-[r:{relationship_type}]->() RETURN r"
        return self.query(query)
