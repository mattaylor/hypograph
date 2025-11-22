# Hypograph Python API Reference

## Adapters

### `CypherAdapter`
Generic adapter for Cypher-compatible databases (e.g., Neo4j).

```python
from hypograph.adapters.cypher_adapter import CypherAdapter
adapter = CypherAdapter()
adapter.connect("bolt://localhost:7687", auth=("user", "pass"))
```

### `FalkorDBAdapter`
Adapter optimized for FalkorDB.

```python
from hypograph.adapters.falkordb_adapter import FalkorDBAdapter
adapter = FalkorDBAdapter()
adapter.connect("localhost", port=6379)
```

## Statistical Methods

### Inference (`hypograph.stats.inference`)

- **`calculate_density(adapter, weight_property=None) -> float`**
  Calculates graph density. If `weight_property` is provided, calculates weighted density.

- **`get_degree_distribution(adapter, weight_property=None) -> Dict[float, int]`**
  Returns a dictionary mapping degree (or weighted strength) to node count.

### Hypothesis Testing (`hypograph.stats.hypothesis`)

- **`z_test_density(adapter, expected_val, n_nodes, weight_property=None) -> (z_score, p_value)`**
  Performs a Z-test comparing observed density against an expected value.

### Community Detection (`hypograph.stats.community`)

- **`detect_communities_label_propagation(adapter, write_property="community", weight_property=None)`**
  Runs Label Propagation algorithm.

- **`get_modularity(adapter, community_property="community", weight_property=None) -> float`**
  Calculates modularity score for a given partition.

### Centrality (`hypograph.stats.centrality`)

- **`degree_centrality(adapter, direction="BOTH") -> Dict[str, float]`**
  Calculates normalized degree centrality. Direction can be "IN", "OUT", or "BOTH".

- **`pagerank(adapter, damping=0.85, iterations=20) -> Dict[str, float]`**
  Calculates PageRank scores.

- **`betweenness_centrality(adapter) -> Dict[str, float]`**
  Calculates Betweenness Centrality scores.

### Advanced Hypothesis (`hypograph.stats.advanced_hypothesis`)

- **`anova_test(adapter, group_property, metric_property) -> (f_stat, p_val)`**
  Performs One-Way ANOVA.

- **`chi_square_test(adapter, property_a, property_b) -> (chi2, p, dof, expected)`**
  Performs Chi-Square test of independence.

- **`correlation_test(adapter, property_a, property_b, method='pearson') -> (corr, p_val)`**
  Calculates correlation between two properties.

## Importer (`hypograph.importer`)

- **`CSVImporter(adapter)`**
  - `import_nodes(csv_path, label, id_col="id", property_cols=None)`
  - `import_edges(csv_path, source_col, target_col, relationship_type, ...)`
