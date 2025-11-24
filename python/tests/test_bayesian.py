import unittest
from unittest.mock import MagicMock
from hypograph.stats.bayesian import beta_binomial_test, bayes_factor_density

class TestBayesian(unittest.TestCase):
    def test_beta_binomial(self):
        adapter = MagicMock()
        # Mock 4 nodes, 3 edges
        # Possible edges = 4*3 = 12
        # Density = 3/12 = 0.25
        
        def query_side_effect(query, params=None):
            if "count(n)" in query:
                return [{'count': 4}]
            if "count(r)" in query:
                return [{'count': 3}]
            return []
        adapter.query.side_effect = query_side_effect
        
        # Prior: alpha=1, beta=1 (Uniform)
        # Posterior: alpha = 1+3=4, beta = 1+(12-3)=10
        # Mean = 4/14 = 0.2857
        
        res = beta_binomial_test(adapter)
        self.assertEqual(res['alpha_post'], 4)
        self.assertEqual(res['beta_post'], 10)
        self.assertAlmostEqual(res['mean'], 4/14)
        
    def test_bayes_factor(self):
        adapter = MagicMock()
        # Mock 5 nodes, 20 possible edges (directed)
        # Observed 18 edges. Density = 0.9
        
        def query_side_effect(query, params=None):
            if "count(n)" in query:
                return [{'count': 5}]
            if "count(r)" in query:
                return [{'count': 18}]
            return []
        adapter.query.side_effect = query_side_effect
        
        # Test H1: density > 0.5 vs H2: density <= 0.5
        # Prior (1,1): P(theta > 0.5) = 0.5. Odds = 1.
        # Posterior (1+18, 1+2) = Beta(19, 3). Mean ~ 0.86.
        # P(theta > 0.5) should be very high.
        
        bf = bayes_factor_density(adapter, theta_0=0.5)
        self.assertTrue(bf > 10.0)

if __name__ == '__main__':
    unittest.main()
