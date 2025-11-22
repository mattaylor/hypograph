from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class GraphAdapter(ABC):
    """
    Abstract base class for graph database adapters.
    """

    @abstractmethod
    def connect(self, uri: str, auth: Any = None):
        """
        Connect to the database.
        """
        pass

    @abstractmethod
    def close(self):
        """
        Close the connection.
        """
        pass

    @abstractmethod
    def query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return the results as a list of dictionaries.
        """
        pass

    @abstractmethod
    def get_nodes(self, label: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve nodes, optionally filtered by label.
        """
        pass

    @abstractmethod
    def get_edges(self, relationship_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve edges, optionally filtered by relationship type.
        """
        pass
