import { GraphAdapter } from '../adapters/GraphAdapter';

export async function detectCommunitiesLabelPropagation(adapter: GraphAdapter, writeProperty: string = "community", weightProperty?: string, nodeFilter?: string, edgeFilter?: string) {
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
    
    let edgeQuery = "";
    let relationshipWeightProperty = "";
    
    if (weightProperty) {
        edgeQuery = `MATCH (n)-[r]->(m) ${edgeWhere} RETURN id(n) as source, id(m) as target, r.${weightProperty} as weight`;
        relationshipWeightProperty = "weight";
    } else {
        edgeQuery = `MATCH (n)-[r]->(m) ${edgeWhere} RETURN id(n) as source, id(m) as target`;
    }

    const query = `
    CALL gds.labelPropagation.write({
        nodeQuery: "${nodeQuery}",
        relationshipQuery: "${edgeQuery}",
        writeProperty: "${writeProperty}"
        ${relationshipWeightProperty ? `, relationshipWeightProperty: "${relationshipWeightProperty}"` : ''}
    })
    YIELD nodeCount, communityCount, ranIterations, didConverge
    RETURN nodeCount, communityCount, ranIterations, didConverge
    `;
    return adapter.query(query);
}

export async function getModularity(adapter: GraphAdapter, communityProperty: string = "community", weightProperty?: string, nodeFilter?: string, edgeFilter?: string): Promise<number> {
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
    
    // Total weight M
    let mQuery = "";
    if (weightProperty) {
        mQuery = `MATCH (n)-[r]->(m) ${nodeWhere} ${edgeWhere ? 'AND ' + edgeWhere.substring(6) : ''} RETURN sum(r.${weightProperty}) as m`;
    } else {
        mQuery = `MATCH (n)-[r]->(m) ${nodeWhere} ${edgeWhere ? 'AND ' + edgeWhere.substring(6) : ''} RETURN count(r) as m`;
    }
    
    const mRes = await adapter.query(mQuery);
    const m = Number(mRes[0]?.m || 0);
    
    if (m === 0) return 0.0;
    
    const wExpr = weightProperty ? `r.${weightProperty}` : "1";
    
    // e_cc query
    const eCcQuery = `
    MATCH (n)-[r]->(m)
    ${nodeWhere}
    AND n.${communityProperty} = m.${communityProperty}
    AND ${nodeFilter ? nodeFilter.replace(/n/g, 'm') : 'true'}
    AND ${edgeFilter ? edgeFilter : 'true'}
    RETURN n.${communityProperty} as comm, sum(${wExpr}) as weight
    `;
    
    // a_c query
    const aCQuery = `
    MATCH (n) ${nodeWhere}
    OPTIONAL MATCH (n)-[r]-(m)
    WHERE ${nodeFilter ? nodeFilter.replace(/n/g, 'm') : 'true'}
    AND ${edgeFilter ? edgeFilter : 'true'}
    RETURN n.${communityProperty} as comm, sum(${wExpr}) as degree
    `;
    
    const eCcRes = await adapter.query(eCcQuery);
    const aCRes = await adapter.query(aCQuery);
    
    const eCcMap: Record<string, number> = {};
    for (const row of eCcRes) eCcMap[String(row.comm)] = Number(row.weight);
    
    const aCMap: Record<string, number> = {};
    for (const row of aCRes) aCMap[String(row.comm)] = Number(row.degree);
    
    const communities = new Set([...Object.keys(eCcMap), ...Object.keys(aCMap)]);
    
    let modularity = 0.0;
    for (const comm of communities) {
        const e = (eCcMap[comm] || 0) / m;
        const a = (aCMap[comm] || 0) / (2 * m);
        modularity += e - Math.pow(a, 2);
    }
    
    return modularity;
}
