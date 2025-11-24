import { GraphAdapter } from '../adapters/GraphAdapter';
import { calculateDensity } from './inference';

import { jStat } from 'jstat';

export async function zTestDensity(adapter: GraphAdapter, expectedVal: number, nNodes: number, weightProperty?: string, nodeFilter?: string, edgeFilter?: string): Promise<{ zScore: number, pValue: number }> {
    // Recalculate density with filters
    const observedDensity = await calculateDensity(adapter, weightProperty, nodeFilter, edgeFilter);
    
    const possibleEdges = nNodes * (nNodes - 1) / 2;
    if (possibleEdges <= 0) {
        return { zScore: 0.0, pValue: 1.0 };
    }
    
    // Standard Error (Simplified)
    const se = Math.sqrt(expectedVal * (1 - expectedVal) / possibleEdges);
    
    if (se === 0) {
        return { zScore: 0.0, pValue: 0.0 };
    }
    
    const zScore = (observedDensity - expectedVal) / se;
    
    // P-value (Two-tailed) using jStat
    const pValue = 2 * (1 - jStat.normal.cdf(Math.abs(zScore), 0, 1));
    
    return { zScore, pValue };
}

export async function anovaTest(adapter: GraphAdapter, groupProperty: string, metricProperty: string, nodeFilter?: string): Promise<{ fStat: number, pValue: number }> {
    const nodeWhere = nodeFilter ? `WHERE ${nodeFilter} AND` : "WHERE";
    
    const query = `
    MATCH (n)
    ${nodeWhere} n.${groupProperty} IS NOT NULL AND n.${metricProperty} IS NOT NULL
    RETURN n.${groupProperty} as group, n.${metricProperty} as value
    `;
    const results = await adapter.query(query);
    
    const groups: Record<string, number[]> = {};
    for (const row of results) {
        const g = String(row.group);
        const val = Number(row.value);
        if (!groups[g]) groups[g] = [];
        groups[g].push(val);
    }
    
    const groupValues = Object.values(groups);
    if (groupValues.length < 2) {
        throw new Error("Need at least 2 groups for ANOVA");
    }
    
    const fStat = jStat.anovaftest(...groupValues);
    
    const k = groupValues.length;
    const N = groupValues.reduce((sum, g) => sum + g.length, 0);
    const df1 = k - 1;
    const df2 = N - k;
    
    const pValue = 1 - jStat.centralF.cdf(fStat, df1, df2);
    
    return { fStat, pValue };
}

export async function correlationTest(adapter: GraphAdapter, propertyA: string, propertyB: string, nodeFilter?: string): Promise<{ correlation: number, pValue: number }> {
    const nodeWhere = nodeFilter ? `WHERE ${nodeFilter} AND` : "WHERE";
    
    const query = `
    MATCH (n)
    ${nodeWhere} n.${propertyA} IS NOT NULL AND n.${propertyB} IS NOT NULL
    RETURN n.${propertyA} as a, n.${propertyB} as b
    `;
    const results = await adapter.query(query);
    
    const aVals = results.map(r => Number(r.a));
    const bVals = results.map(r => Number(r.b));
    
    if (aVals.length < 2) return { correlation: 0, pValue: 1 };
    
    const correlation = jStat.corrcoeff(aVals, bVals);
    
    const n = aVals.length;
    const t = correlation * Math.sqrt((n - 2) / (1 - correlation * correlation));
    const pValue = 2 * (1 - jStat.studentt.cdf(Math.abs(t), n - 2));
    
    return { correlation, pValue };
}

export async function chiSquareTest(adapter: GraphAdapter, propertyA: string, propertyB: string, nodeFilter?: string): Promise<{ chi2: number, pValue: number, dof: number }> {
    const nodeWhere = nodeFilter ? `WHERE ${nodeFilter} AND` : "WHERE";
    
    const query = `
    MATCH (n)
    ${nodeWhere} n.${propertyA} IS NOT NULL AND n.${propertyB} IS NOT NULL
    RETURN n.${propertyA} as a, n.${propertyB} as b, count(n) as count
    `;
    const results = await adapter.query(query);
    
    const aVals = Array.from(new Set(results.map(r => String(r.a)))).sort();
    const bVals = Array.from(new Set(results.map(r => String(r.b)))).sort();
    
    const aMap = new Map(aVals.map((v, i) => [v, i]));
    const bMap = new Map(bVals.map((v, i) => [v, i]));
    
    const table: number[][] = Array(aVals.length).fill(0).map(() => Array(bVals.length).fill(0));
    
    for (const row of results) {
        const i = aMap.get(String(row.a))!;
        const j = bMap.get(String(row.b))!;
        table[i][j] = Number(row.count);
    }
    
    let total = 0;
    const rowTotals = Array(aVals.length).fill(0);
    const colTotals = Array(bVals.length).fill(0);
    
    for (let i = 0; i < aVals.length; i++) {
        for (let j = 0; j < bVals.length; j++) {
            const val = table[i][j];
            total += val;
            rowTotals[i] += val;
            colTotals[j] += val;
        }
    }
    
    let chi2 = 0;
    for (let i = 0; i < aVals.length; i++) {
        for (let j = 0; j < bVals.length; j++) {
            const expected = (rowTotals[i] * colTotals[j]) / total;
            if (expected > 0) {
                const obs = table[i][j];
                chi2 += Math.pow(obs - expected, 2) / expected;
            }
        }
    }
    
    const dof = (aVals.length - 1) * (bVals.length - 1);
    const pValue = 1 - jStat.chisquare.cdf(chi2, dof);
    
    return { chi2, pValue, dof };
}
