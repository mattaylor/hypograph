import { betaBinomialTest, bayesFactorDensity } from '../stats/bayesian';

class MockAdapter {
    async query(q: string): Promise<any[]> {
        if (q.includes("count(n)")) return [{ count: 5 }];
        if (q.includes("count(r)")) return [{ count: 18 }];
        return [];
    }
    async connect() {}
    async close() {}
    async getNodes() { return []; }
    async getEdges() { return []; }
}

async function testBayesian() {
    const adapter = new MockAdapter();
    
    // Test Beta Binomial
    const res = await betaBinomialTest(adapter as any);
    // Nodes=5, Possible=20. Edges=18.
    // Alpha: 1+18=19, Beta: 1+(20-18)=3
    if (res.alphaPost === 19 && res.betaPost === 3) {
        console.log("Beta-Binomial test passed");
    } else {
        console.error(`Beta-Binomial test failed: ${JSON.stringify(res)}`);
        process.exit(1);
    }
    
    // Test Bayes Factor
    // H1: density > 0.5
    const bf = await bayesFactorDensity(adapter as any, 0.5);
    console.log(`Bayes Factor: ${bf}`);
    if (bf > 10.0) {
        console.log("Bayes Factor test passed");
    } else {
        console.error(`Bayes Factor test failed: ${bf}`);
        process.exit(1);
    }
}

testBayesian().catch(e => {
    console.error(e);
    process.exit(1);
});
