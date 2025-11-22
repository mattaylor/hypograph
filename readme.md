# Hypograph

Hypograph is a dual-language (Python and JavaScript/TypeScript) library for statistical inference, hypothesis testing, and community detection in graph networks. It supports generic Cypher-compatible databases (like Neo4j) and has native optimizations for FalkorDB.

## Features

- **Statistical Inference**: Calculate graph density, degree distribution, and more.
- **Hypothesis Testing**: Z-tests for graph properties against null models.
- **Community Detection**: Label Propagation and Modularity analysis.
- **Weighted Graphs**: Full support for weighted edges in all statistical methods.
- **Data Import**: Utilities to import nodes and edges from CSV files.
- **Adapters**: Abstracted database interface for easy switching between backends.

## Structure

- `python/`: Python implementation.
- `js/`: JavaScript/TypeScript implementation.
- `data/`: Sample data files.

## Getting Started

### Python

```bash
cd python
pip install .
```

### JavaScript

```bash
cd js
npm install
npm run build
```

## Usage Examples

See the `tests` directories in each language folder for usage examples.
