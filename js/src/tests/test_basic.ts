import { CypherAdapter } from '../adapters/CypherAdapter';
import { calculateDensity } from '../stats/inference';
import { zTestDensity, anovaTest, chiSquareTest, correlationTest } from '../stats/hypothesis';

// Mocking is a bit more complex in raw TS without jest setup, 
// so we will create a manual mock class for this basic verification.

class MockAdapter {
    async query(q: string): Promise<any[]> {
        if (q.includes("count(n)")) return [{ count: 4 }];
        if (q.includes("count(r)")) return [{ count: 3 }];
        if (q.includes("sum(r.weight)")) return [{ count: 1.5 }];
        return [];
    }
    async connect() {}
    async close() {}
    async getNodes() { return []; }
    async getEdges() { return []; }
}

async function testDensity() {
    const adapter = new MockAdapter();
    const density = await calculateDensity(adapter as any);
    if (density === 0.5) {
        console.log("Density test passed");
    } else {
        console.error(`Density test failed: expected 0.5, got ${density}`);
        process.exit(1);
    }
    
    const weightedDensity = await calculateDensity(adapter as any, "weight");
    if (weightedDensity === 0.25) {
        console.log("Weighted density test passed");
    } else {
        console.error(`Weighted density test failed: expected 0.25, got ${weightedDensity}`);
        process.exit(1);
    }

    // Test Correlation
    const corrAdapter = {
        query: async () => [
            { a: 1, b: 2 },
            { a: 2, b: 4 },
            { a: 3, b: 6 }
        ]
    };
    
    const { correlationTest } = require('../stats/hypothesis');
    const { correlation } = await correlationTest(corrAdapter as any, "propA", "propB");
    
    if (Math.abs(correlation - 1.0) < 0.001) {
        console.log("Correlation test passed");
    } else {
        console.error(`Correlation test failed: expected 1.0, got ${correlation}`);
        process.exit(1);
    }

    // Test Subgraph Filters
    const filterAdapter = new MockAdapter();
    // Override query for filters
    filterAdapter.query = async (q: string) => {
        if (q.includes("WHERE n.age > 20") && q.includes("count(n)")) return [{ count: 2 }];
        // The query construction logic puts parentheses around filters and joins with AND
        // Expected: WHERE (n.age > 20) AND (m.age > 20) AND (r.weight > 0.5)
        if (q.includes("(n.age > 20)") && q.includes("(m.age > 20)") && q.includes("(r.weight > 0.5)")) return [{ count: 1 }];
        return [];
    };
    
    const filterDensity = await calculateDensity(filterAdapter as any, undefined, "n.age > 20", "r.weight > 0.5");
    // Density = 2 * 1 / (2 * 1) = 1.0
    if (filterDensity === 1.0) {
        console.log("Subgraph filter test passed");
    } else {
        console.error(`Subgraph filter test failed: expected 1.0, got ${filterDensity}`);
        process.exit(1);
    }
}

testDensity().catch(e => {
    console.error(e);
    process.exit(1);
});
