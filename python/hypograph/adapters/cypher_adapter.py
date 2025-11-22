from typing import Any, Dict, List, Optional
from neo4j import GraphDatabase
from .base import GraphAdapter

class CypherAdapter(GraphAdapter):
    """
    Adapter for generic Cypher-compatible databases using the neo4j driver.
    """

    def __init__(self):
        self.driver = None

    def connect(self, uri: str, auth: Any = None):
        self.driver = GraphDatabase.driver(uri, auth=auth)

    def close(self):
        if self.driver:
            self.driver.close()

    def query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not self.driver:
            raise ConnectionError("Not connected to the database.")
        
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]

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
