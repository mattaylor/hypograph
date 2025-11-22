# Hypograph JavaScript API Reference

## Adapters

### `CypherAdapter`
Generic adapter for Cypher-compatible databases.

```typescript
import { CypherAdapter } from 'hypograph';
const adapter = new CypherAdapter();
await adapter.connect("bolt://localhost:7687", { user: "neo4j", password: "password" });
```

### `FalkorDBAdapter`
Adapter optimized for FalkorDB.

```typescript
import { FalkorDBAdapter } from 'hypograph';
const adapter = new FalkorDBAdapter();
await adapter.connect("localhost", { port: 6379 });
```

## Statistical Methods

### Inference

- **`calculateDensity(adapter, weightProperty?) -> Promise<number>`**
  Calculates graph density.

- **`getDegreeDistribution(adapter, weightProperty?) -> Promise<Record<number, number>>`**
  Returns degree distribution.

### Hypothesis Testing

- **`zTestDensity(adapter, expectedVal, nNodes, weightProperty?) -> Promise<{ zScore, pValue }>`**
  Performs Z-test on density.

### Community Detection

- **`detectCommunitiesLabelPropagation(adapter, writeProperty="community", weightProperty?)`**
  Runs Label Propagation.

- **`getModularity(adapter, communityProperty="community", weightProperty?) -> Promise<number>`**
  Calculates modularity.

### Centrality

- **`degreeCentrality(adapter, direction="BOTH") -> Promise<Record<string, number>>`**
  Calculates normalized degree centrality.

- **`pageRank(adapter, damping=0.85, iterations=20) -> Promise<Record<string, number>>`**
  Calculates PageRank.

- **`betweennessCentrality(adapter) -> Promise<Record<string, number>>`**
  Calculates Betweenness Centrality.

### Advanced Hypothesis

- **`anovaTest(adapter, groupProperty, metricProperty) -> Promise<{ fStat, pValue }>`**
  Performs One-Way ANOVA.

- **`correlationTest(adapter, propertyA, propertyB) -> Promise<{ correlation }>`**
  Calculates correlation.

## Importer

### `CSVImporter`

```typescript
import { CSVImporter } from 'hypograph';
const importer = new CSVImporter(adapter);
await importer.importNodes("path/to/nodes.csv", "Person");
await importer.importEdges("path/to/edges.csv", "source", "target", "KNOWS", ...);
```
