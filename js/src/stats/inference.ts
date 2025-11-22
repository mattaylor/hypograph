import { GraphAdapter } from '../adapters/GraphAdapter';

export async function calculateDensity(adapter: GraphAdapter, weightProperty?: string, nodeFilter?: string, edgeFilter?: string): Promise<number> {
    const nodeWhere = nodeFilter ? `WHERE ${nodeFilter}` : "";
    const nodeCountRes = await adapter.query(`MATCH (n) ${nodeWhere} RETURN count(n) as count`);
    
    const whereClauses: string[] = [];
    if (nodeFilter) {
        whereClauses.push(`(${nodeFilter})`);
        // Replace 'n' with 'm' for target node filter
        const mFilter = nodeFilter.replace(/n/g, "m");
        whereClauses.push(`(${mFilter})`);
    }
    if (edgeFilter) {
        whereClauses.push(`(${edgeFilter})`);
    }
    
    const edgeWhere = whereClauses.length > 0 ? "WHERE " + whereClauses.join(" AND ") : "";
    
    let edgeQuery = "";
    if (weightProperty) {
        edgeQuery = `MATCH (n)-[r]->(m) ${edgeWhere} RETURN sum(r.${weightProperty}) as count`;
    } else {
        edgeQuery = `MATCH (n)-[r]->(m) ${edgeWhere} RETURN count(r) as count`;
    }
    
    const edgeCountRes = await adapter.query(edgeQuery);

    const nodeCount = Number(nodeCountRes[0]?.count || 0);
    const edgeVal = Number(edgeCountRes[0]?.count || 0);

    if (nodeCount < 2) {
        return 0.0;
    }

    return (2 * edgeVal) / (nodeCount * (nodeCount - 1));
}

export async function getDegreeDistribution(adapter: GraphAdapter, weightProperty?: string, nodeFilter?: string, edgeFilter?: string): Promise<Record<number, number>> {
    const nodeWhere = nodeFilter ? `WHERE ${nodeFilter}` : "";
    
    const edgeConditions: string[] = [];
    if (nodeFilter) {
        const mFilter = nodeFilter.replace(/n/g, "m");
        edgeConditions.push(`(${mFilter})`);
    }
    if (edgeFilter) {
        edgeConditions.push(`(${edgeFilter})`);
    }
    
    const edgeWhere = edgeConditions.length > 0 ? "WHERE " + edgeConditions.join(" AND ") : "";
    
    let query = "";
    if (weightProperty) {
        query = `
        MATCH (n) ${nodeWhere}
        OPTIONAL MATCH (n)-[r]-(m)
        ${edgeWhere}
        WITH n, sum(coalesce(r.${weightProperty}, 0)) as degree
        RETURN degree, count(n) as count
        ORDER BY degree
        `;
    } else {
        query = `
        MATCH (n) ${nodeWhere}
        OPTIONAL MATCH (n)-[r]-(m)
        ${edgeWhere}
        WITH n, count(r) as degree
        RETURN degree, count(n) as count
        ORDER BY degree
        `;
    }
    
    const results = await adapter.query(query);
    
    const distribution: Record<number, number> = {};
    for (const row of results) {
        const degree = Number(row.degree);
        const count = Number(row.count);
        distribution[degree] = count;
    }
    
    return distribution;
}
