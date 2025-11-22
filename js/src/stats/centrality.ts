import { GraphAdapter } from '../adapters/GraphAdapter';

export async function degreeCentrality(adapter: GraphAdapter, direction: "IN" | "OUT" | "BOTH" = "BOTH", nodeFilter?: string, edgeFilter?: string): Promise<Record<string, number>> {
    const nodeWhere = nodeFilter ? `WHERE ${nodeFilter}` : "";
    const countRes = await adapter.query(`MATCH (n) ${nodeWhere} RETURN count(n) as count`);
    const nNodes = Number(countRes[0]?.count || 0);

    if (nNodes <= 1) {
        return {};
    }

    let neighbor = "m";
    let pattern = "";
    if (direction === "IN") {
        pattern = `(n)<-[r]-(${neighbor})`;
    } else if (direction === "OUT") {
        pattern = `(n)-[r]->(${neighbor})`;
    } else {
        pattern = `(n)-[r]-(${neighbor})`;
    }
    
    const whereClauses: string[] = [];
    if (nodeFilter) {
        whereClauses.push(`(${nodeFilter})`);
        whereClauses.push(`(${nodeFilter.replace(/n/g, neighbor)})`);
    }
    if (edgeFilter) {
        whereClauses.push(`(${edgeFilter})`);
    }
    
    const fullWhere = whereClauses.length > 0 ? "WHERE " + whereClauses.join(" AND ") : "";

    const query = `MATCH ${pattern} ${fullWhere} RETURN id(n) as id, count(r) as degree`;

    const results = await adapter.query(query);
    const centrality: Record<string, number> = {};

    for (const row of results) {
        const id = String(row.id);
        const degree = Number(row.degree);
        centrality[id] = degree / (nNodes - 1);
    }

    return centrality;
}

export async function pageRank(adapter: GraphAdapter, damping: number = 0.85, iterations: number = 20, nodeFilter?: string, edgeFilter?: string): Promise<Record<string, number>> {
    try {
        const nodeQuery = nodeFilter ? `MATCH (n) WHERE ${nodeFilter} RETURN id(n) as id` : "MATCH (n) RETURN id(n) as id";
        
        const edgeConditions: string[] = [];
        if (nodeFilter) {
            const mFilter = nodeFilter.replace(/n/g, "m");
            edgeConditions.push(`(${nodeFilter})`);
            edgeConditions.push(`(${mFilter})`);
        }
        if (edgeFilter) {
            edgeConditions.push(`(${edgeFilter})`);
        }
        const edgeWhere = edgeConditions.length > 0 ? "WHERE " + edgeConditions.join(" AND ") : "";
        
        const edgeQuery = `MATCH (n)-[r]->(m) ${edgeWhere} RETURN id(n) as source, id(m) as target`;

        const query = `
        CALL gds.pageRank.stream({
            nodeQuery: "${nodeQuery}",
            relationshipQuery: "${edgeQuery}",
            dampingFactor: ${damping},
            maxIterations: ${iterations}
        })
        YIELD nodeId, score
        RETURN nodeId, score
        `;
        const results = await adapter.query(query);
        const ranks: Record<string, number> = {};
        for (const row of results) {
            ranks[String(row.nodeId)] = Number(row.score);
        }
        return ranks;
    } catch (e) {
        console.warn("Native PageRank not available. Returning degree centrality as fallback.");
        return degreeCentrality(adapter, "BOTH", nodeFilter, edgeFilter);
    }
}

export async function betweennessCentrality(adapter: GraphAdapter, nodeFilter?: string, edgeFilter?: string): Promise<Record<string, number>> {
    try {
        const nodeQuery = nodeFilter ? `MATCH (n) WHERE ${nodeFilter} RETURN id(n) as id` : "MATCH (n) RETURN id(n) as id";
        
        const edgeConditions: string[] = [];
        if (nodeFilter) {
            const mFilter = nodeFilter.replace(/n/g, "m");
            edgeConditions.push(`(${nodeFilter})`);
            edgeConditions.push(`(${mFilter})`);
        }
        if (edgeFilter) {
            edgeConditions.push(`(${edgeFilter})`);
        }
        const edgeWhere = edgeConditions.length > 0 ? "WHERE " + edgeConditions.join(" AND ") : "";
        
        const edgeQuery = `MATCH (n)-[r]->(m) ${edgeWhere} RETURN id(n) as source, id(m) as target`;

        const query = `
        CALL gds.betweenness.stream({
            nodeQuery: "${nodeQuery}",
            relationshipQuery: "${edgeQuery}"
        })
        YIELD nodeId, score
        RETURN nodeId, score
        `;
        const results = await adapter.query(query);
        const centrality: Record<string, number> = {};
        for (const row of results) {
            centrality[String(row.nodeId)] = Number(row.score);
        }
        return centrality;
    } catch (e) {
        console.warn("Native Betweenness not available.");
        return {};
    }
}
