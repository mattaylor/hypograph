import csv
from typing import List, Dict, Any
from ..adapters.base import GraphAdapter

class CSVImporter:
    def __init__(self, adapter: GraphAdapter):
        self.adapter = adapter

    def import_nodes(self, csv_path: str, label: str, id_col: str = "id", property_cols: List[str] = None):
        """
        Import nodes from a CSV file.
        """
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                props = {}
                if property_cols:
                    for col in property_cols:
                        if col in row:
                            props[col] = row[col]
                else:
                    # Import all columns except id as properties
                    props = {k: v for k, v in row.items() if k != id_col}
                
                # Construct query
                # Using MERGE to avoid duplicates based on ID
                # Assuming id_col is the unique identifier
                
                # Sanitize inputs (basic)
                # In production, use parameters!
                
                prop_str = ", ".join([f"{k}: ${k}" for k in props.keys()])
                if prop_str:
                    prop_str = ", " + prop_str
                
                query = f"MERGE (n:{label} {{ {id_col}: $id_val }}) SET n += $props"
                
                self.adapter.query(query, {"id_val": row[id_col], "props": props})

    def import_edges(self, csv_path: str, source_col: str, target_col: str, relationship_type: str, 
                     source_label: str, target_label: str, source_id_col: str = "id", target_id_col: str = "id",
                     weight_col: str = None, property_cols: List[str] = None):
        """
        Import edges from a CSV file.
        """
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                props = {}
                if weight_col and weight_col in row:
                    try:
                        props[weight_col] = float(row[weight_col])
                    except ValueError:
                        props[weight_col] = 0.0
                        
                if property_cols:
                    for col in property_cols:
                        if col in row and col != weight_col:
                            props[col] = row[col]
                
                query = f"""
                MATCH (a:{source_label} {{ {source_id_col}: $source_id }})
                MATCH (b:{target_label} {{ {target_id_col}: $target_id }})
                MERGE (a)-[r:{relationship_type}]->(b)
                SET r += $props
                """
                
                self.adapter.query(query, {
                    "source_id": row[source_col],
                    "target_id": row[target_col],
                    "props": props
                })
