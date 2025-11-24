import { GraphAdapter } from '../adapters/GraphAdapter';
import { jStat } from 'jstat';

export interface BetaBinomialResult {
    mean: number;
    ciLow: number;
    ciHigh: number;
    alphaPost: number;
    betaPost: number;
}

export async function betaBinomialTest(
    adapter: GraphAdapter, 
    alphaPrior: number = 1.0, 
    betaPrior: number = 1.0,
    nodeFilter?: string,
    edgeFilter?: string
): Promise<BetaBinomialResult> {
    const nodeWhere = nodeFilter ? `WHERE ${nodeFilter}` : "";
    const nodeCountRes = await adapter.query(`MATCH (n) ${nodeWhere} RETURN count(n) as count`);
    const nNodes = Number(nodeCountRes[0]?.count || 0);

    if (nNodes < 2) {
        return {
            mean: 0.0, ciLow: 0.0, ciHigh: 0.0,
            alphaPost: alphaPrior, betaPost: betaPrior
        };
    }

    const possibleEdges = nNodes * (nNodes - 1); // Directed

    const whereClauses: string[] = [];
    if (nodeFilter) {
        whereClauses.push(`(${nodeFilter})`);
        whereClauses.push(`(${nodeFilter.replace(/n/g, "m")})`);
    }
    if (edgeFilter) {
        whereClauses.push(`(${edgeFilter})`);
    }
    
    const edgeWhere = whereClauses.length > 0 ? "WHERE " + whereClauses.join(" AND ") : "";
    const edgeCountRes = await adapter.query(`MATCH (n)-[r]->(m) ${edgeWhere} RETURN count(r) as count`);
    const nEdges = Number(edgeCountRes[0]?.count || 0);

    const alphaPost = alphaPrior + nEdges;
    const betaPost = betaPrior + (possibleEdges - nEdges);

    const mean = alphaPost / (alphaPost + betaPost);
    
    // jStat.beta.inv(p, alpha, beta) for quantiles
    const ciLow = jStat.beta.inv(0.025, alphaPost, betaPost);
    const ciHigh = jStat.beta.inv(0.975, alphaPost, betaPost);

    return {
        mean,
        ciLow,
        ciHigh,
        alphaPost,
        betaPost
    };
}

export async function bayesFactorDensity(
    adapter: GraphAdapter, 
    theta0: number,
    alphaPrior: number = 1.0, 
    betaPrior: number = 1.0,
    nodeFilter?: string,
    edgeFilter?: string
): Promise<number> {
    const stats = await betaBinomialTest(adapter, alphaPrior, betaPrior, nodeFilter, edgeFilter);
    const aPost = stats.alphaPost;
    const bPost = stats.betaPost;

    // Prior odds
    // P(theta > theta0) = 1 - CDF(theta0)
    const priorProbH1 = 1 - jStat.beta.cdf(theta0, alphaPrior, betaPrior);
    const priorProbH2 = jStat.beta.cdf(theta0, alphaPrior, betaPrior);
    
    if (priorProbH2 === 0) return Infinity;
    const priorOdds = priorProbH1 / priorProbH2;

    // Posterior odds
    const postProbH1 = 1 - jStat.beta.cdf(theta0, aPost, bPost);
    const postProbH2 = jStat.beta.cdf(theta0, aPost, bPost);

    if (postProbH2 === 0) return Infinity;
    const postOdds = postProbH1 / postProbH2;

    if (priorOdds === 0) return Infinity;
    return postOdds / priorOdds;
}
