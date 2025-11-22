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
