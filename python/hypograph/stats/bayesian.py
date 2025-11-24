from scipy.stats import beta
import numpy as np
from hypograph.adapters.base import GraphAdapter

def beta_binomial_test(adapter: GraphAdapter, alpha_prior: float = 1.0, beta_prior: float = 1.0, 
                       node_filter: str = None, edge_filter: str = None):
    """
    Estimates graph density using a Beta-Binomial model.
    
    Args:
        adapter: GraphAdapter instance.
        alpha_prior: Prior alpha parameter for Beta distribution (default 1.0).
        beta_prior: Prior beta parameter for Beta distribution (default 1.0).
        node_filter: Optional Cypher filter for nodes.
        edge_filter: Optional Cypher filter for edges.
        
    Returns:
        dict: {
            'mean': Posterior mean,
            'ci_low': 95% Credible Interval lower bound,
            'ci_high': 95% Credible Interval upper bound,
            'alpha_post': Posterior alpha,
            'beta_post': Posterior beta
        }
    """
    node_where = f"WHERE {node_filter}" if node_filter else ""
    node_query = f"MATCH (n) {node_where} RETURN count(n) as count"
    node_res = adapter.query(node_query)
    n_nodes = int(node_res[0]['count'])
    
    if n_nodes < 2:
        return {
            'mean': 0.0, 'ci_low': 0.0, 'ci_high': 0.0,
            'alpha_post': alpha_prior, 'beta_post': beta_prior
        }
        
    possible_edges = n_nodes * (n_nodes - 1) # Directed
    
    # Edge count
    where_clauses = []
    if node_filter:
        where_clauses.append(f"({node_filter})")
        # For induced subgraph, target node must also match filter
        where_clauses.append(f"({node_filter.replace('n', 'm')})")
    if edge_filter:
        where_clauses.append(f"({edge_filter})")
        
    edge_where = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    edge_query = f"MATCH (n)-[r]->(m) {edge_where} RETURN count(r) as count"
    edge_res = adapter.query(edge_query)
    n_edges = int(edge_res[0]['count'])
    
    # Posterior parameters
    alpha_post = alpha_prior + n_edges
    beta_post = beta_prior + (possible_edges - n_edges)
    
    # Statistics
    mean_post = alpha_post / (alpha_post + beta_post)
    ci_low, ci_high = beta.interval(0.95, alpha_post, beta_post)
    
    return {
        'mean': mean_post,
        'ci_low': ci_low,
        'ci_high': ci_high,
        'alpha_post': alpha_post,
        'beta_post': beta_post
    }

def bayes_factor_density(adapter: GraphAdapter, theta_0: float, 
                         alpha_prior: float = 1.0, beta_prior: float = 1.0,
                         node_filter: str = None, edge_filter: str = None):
    """
    Calculates Bayes Factor for H1: density > theta_0 vs H2: density <= theta_0.
    
    Args:
        adapter: GraphAdapter instance.
        theta_0: Threshold density value.
        alpha_prior: Prior alpha.
        beta_prior: Prior beta.
        
    Returns:
        float: Bayes Factor (BF_12). > 1 favors H1.
    """
    # Get posterior parameters
    stats = beta_binomial_test(adapter, alpha_prior, beta_prior, node_filter, edge_filter)
    a_post = stats['alpha_post']
    b_post = stats['beta_post']
    
    # Prior odds
    # P(theta > theta_0 | prior) / P(theta <= theta_0 | prior)
    prior_prob_h1 = 1 - beta.cdf(theta_0, alpha_prior, beta_prior)
    prior_prob_h2 = beta.cdf(theta_0, alpha_prior, beta_prior)
    
    if prior_prob_h2 == 0: return float('inf')
    prior_odds = prior_prob_h1 / prior_prob_h2
    
    # Posterior odds
    post_prob_h1 = 1 - beta.cdf(theta_0, a_post, b_post)
    post_prob_h2 = beta.cdf(theta_0, a_post, b_post)
    
    if post_prob_h2 == 0: return float('inf')
    post_odds = post_prob_h1 / post_prob_h2
    
    # Bayes Factor = Posterior Odds / Prior Odds
    if prior_odds == 0: return float('inf')
    bf = post_odds / prior_odds
    
    return bf
