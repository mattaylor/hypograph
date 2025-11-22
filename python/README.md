# Hypograph (Python)

Python library for graph statistical inference.

## Installation

```bash
pip install .
```

## Usage

### Connecting

```python
from hypograph.adapters.cypher_adapter import CypherAdapter
# or
from hypograph.adapters.falkordb_adapter import FalkorDBAdapter

adapter = CypherAdapter()
adapter.connect("bolt://localhost:7687", auth=("neo4j", "password"))
```

### Statistical Methods

```python
from hypograph.stats.inference import calculate_density
from hypograph.stats.hypothesis import z_test_density

# Weighted density
density = calculate_density(adapter, weight_property="weight")

# Z-test
z_score, p_value = z_test_density(adapter, expected_val=0.5, n_nodes=100, weight_property="weight")
```

### Importing Data

```python
from hypograph.importer import CSVImporter

importer = CSVImporter(adapter)
importer.import_nodes("path/to/nodes.csv", label="Person")
importer.import_edges("path/to/edges.csv", source_col="source", target_col="target", 
                      relationship_type="KNOWS", source_label="Person", target_label="Person",
                      weight_col="weight")
```
