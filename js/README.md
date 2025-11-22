# Hypograph (JavaScript)

TypeScript/JavaScript library for graph statistical inference.

## Installation

```bash
npm install
```

## Usage

### Connecting

```typescript
import { CypherAdapter } from './adapters/CypherAdapter';
// or
import { FalkorDBAdapter } from './adapters/FalkorDBAdapter';

const adapter = new CypherAdapter();
await adapter.connect("bolt://localhost:7687", { user: "neo4j", password: "password" });
```

### Statistical Methods

```typescript
import { calculateDensity } from './stats/inference';
import { zTestDensity } from './stats/hypothesis';

// Weighted density
const density = await calculateDensity(adapter, "weight");

// Z-test
const { zScore, pValue } = await zTestDensity(adapter, 0.5, 100, "weight");
```

### Importing Data

```typescript
import { CSVImporter } from './importer';

const importer = new CSVImporter(adapter);
await importer.importNodes("path/to/nodes.csv", "Person");
await importer.importEdges("path/to/edges.csv", "source", "target", "KNOWS", "Person", "Person", "id", "id", "weight");
```
