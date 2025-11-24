# Hypograph Tutorial: Healthcare Graph Analysis

This tutorial guides you through using **Hypograph** to analyze a healthcare dataset. We will model patients, conditions, and treatments, and perform statistical analysis to uncover insights.

## Prerequisites

- **Python** (3.8+) or **Node.js** (14+)
- **Neo4j** or **FalkorDB** instance running locally.
- **Hypograph** library installed.

## 1. The Dataset

We have provided a sample healthcare dataset in `data/healthcare/`:

- **Nodes**:
    - `Patient`: `id`, `name`, `age`, `gender`, `region`, `recovery_score`
    - `Condition`: `id`, `name`, `severity`
    - `Treatment`: `id`, `name`, `type`
- **Edges**:
    - `(Patient)-[:HAS_CONDITION {since: ...}]->(Condition)`
    - `(Patient)-[:UNDERWENT {outcome_score: ...}]->(Treatment)`

## 2. Setup and Data Import

First, we connect to the database and import the CSV data.

### Python
```python
from hypograph.adapters.cypher_adapter import CypherAdapter
from hypograph.importer import CSVImporter

# Connect
adapter = CypherAdapter("bolt://localhost:7687", "neo4j", "password")
importer = CSVImporter(adapter)

# Import Nodes
importer.import_nodes("data/healthcare/patients.csv", "Patient")
importer.import_nodes("data/healthcare/conditions.csv", "Condition")
importer.import_nodes("data/healthcare/treatments.csv", "Treatment")

# Import Edges
importer.import_edges("data/healthcare/patient_condition_edges.csv", "HAS_CONDITION")
importer.import_edges("data/healthcare/patient_treatment_edges.csv", "UNDERWENT", weight_col="outcome_score")
```

### JavaScript
```typescript
import { CypherAdapter } from 'hypograph/adapters/CypherAdapter';
import { CSVImporter } from 'hypograph/importer';

const adapter = new CypherAdapter("bolt://localhost:7687", "neo4j", "password");
await adapter.connect();
const importer = new CSVImporter(adapter);

await importer.importNodes("data/healthcare/patients.csv", "Patient");
// ... import other files similarly
```

## 3. Statistical Inference

Calculate basic graph properties like density to understand connectivity.

```python
from hypograph.stats.inference import calculate_density

# Overall Density
density = calculate_density(adapter)
print(f"Graph Density: {density}")

# Subgraph Density (Patients > 60)
cohort_filter = "(n:Patient AND toInteger(n.age) > 60) OR n:Condition OR n:Treatment"
cohort_density = calculate_density(adapter, node_filter=cohort_filter)
print(f"Cohort Density: {cohort_density}")
```

## 4. Centrality Analysis

Identify key nodes. For example, which conditions are most prevalent?

```python
from hypograph.stats.centrality import degree_centrality

# In-Degree Centrality for Conditions (incoming edges from Patients)
centrality = degree_centrality(adapter, direction="IN")
# Filter and sort results for 'Condition' nodes in your application logic
```

## 5. Hypothesis Testing

Test statistical hypotheses about your graph data.

### Correlation
Is there a relationship between Patient Age and Recovery Score?

```python
from hypograph.stats.hypothesis import correlation_test

corr, p_val = correlation_test(adapter, "age", "recovery_score", node_filter="n:Patient")
print(f"Correlation: {corr}, p-value: {p_val}")
```

### ANOVA
Does Gender affect Recovery Score?

```python
from hypograph.stats.hypothesis import anova_test

f_stat, p_val = anova_test(adapter, "gender", "recovery_score", node_filter="n:Patient")
print(f"ANOVA: F={f_stat}, p={p_val}")
```

### Chi-Square
Is there an association between Region and Gender?

```python
from hypograph.stats.hypothesis import chi_square_test

chi2, p, dof, expected = chi_square_test(adapter, "region", "gender", node_filter="n:Patient")
print(f"Chi-Square: {chi2}, p={p}")
```

## 6. Bayesian Inference

Estimate graph properties with uncertainty quantification.

### Beta-Binomial Test
Estimate the true density of the graph with a 95% Credible Interval.

```python
from hypograph.stats.bayesian import beta_binomial_test

stats = beta_binomial_test(adapter)
print(f"Posterior Mean Density: {stats['mean']}")
print(f"95% CI: [{stats['ci_low']}, {stats['ci_high']}]")
```

### Bayes Factor
Compare two hypotheses: Is the density greater than 0.5?

```python
from hypograph.stats.bayesian import bayes_factor_density

# H1: density > 0.5 vs H2: density <= 0.5
bf = bayes_factor_density(adapter, theta_0=0.5)
if bf > 1:
    print(f"Evidence favors H1 (BF={bf})")
else:
    print(f"Evidence favors H2 (BF={bf})")
```

## Conclusion

Hypograph provides a powerful toolkit for statistical analysis directly on your graph data, bridging the gap between graph databases and statistical science.
