import unittest
from unittest.mock import MagicMock
from hypograph.adapters.cypher_adapter import CypherAdapter
from hypograph.stats.inference import calculate_density

class TestHypograph(unittest.TestCase):
    def test_cypher_adapter_mock(self):
        adapter = CypherAdapter()
        adapter.driver = MagicMock()
        session = MagicMock()
        adapter.driver.session.return_value.__enter__.return_value = session
        
        # Mock result
        record = MagicMock()
        record.data.return_value = {'n': {'id': 1}}
        session.run.return_value = [record]
        
        result = adapter.query("MATCH (n) RETURN n")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['n']['id'], 1)

    def test_calculate_density(self):
        adapter = MagicMock()
        # Mock node count = 4, edge count = 3
        # Density = 2*3 / (4*3) = 6/12 = 0.5
        
        def query_side_effect(query, params=None):
            if "count(n)" in query:
                return [{'count': 4}]
            if "count(r)" in query:
                return [{'count': 3}]
            if "sum(r.weight)" in query:
                return [{'count': 1.5}] # Weighted sum
            return []
            
        adapter.query.side_effect = query_side_effect
        
        density = calculate_density(adapter)
        self.assertEqual(density, 0.5)
        
        # Weighted density: 2 * 1.5 / 12 = 3/12 = 0.25
        weighted_density = calculate_density(adapter, weight_property="weight")
        self.assertEqual(weighted_density, 0.25)

    def test_degree_centrality(self):
        adapter = MagicMock()
        # Mock 3 nodes
        adapter.query.return_value = [{'count': 3}]
        
        # Mock degrees: n1=2, n2=1, n3=1
        def query_side_effect(query, params=None):
            if "count(n)" in query:
                return [{'count': 3}]
            return [
                {'id': 1, 'degree': 2},
                {'id': 2, 'degree': 1},
                {'id': 3, 'degree': 1}
            ]
        adapter.query.side_effect = query_side_effect
        
        from hypograph.stats.centrality import degree_centrality
        centrality = degree_centrality(adapter)
        
        # Normalized by 2 (N-1)
        self.assertEqual(centrality['1'], 1.0)
        self.assertEqual(centrality['2'], 0.5)

    def test_correlation(self):
        adapter = MagicMock()
        # Perfect correlation
        adapter.query.return_value = [
            {'a': 1, 'b': 2},
            {'a': 2, 'b': 4},
            {'a': 3, 'b': 6}
        ]
        
        from hypograph.stats.hypothesis import z_test_density, anova_test, chi_square_test, correlation_test
        corr, p = correlation_test(adapter, "propA", "propB")
        self.assertAlmostEqual(corr, 1.0)

    def test_subgraph_filters(self):
        adapter = MagicMock()
        
        # Mock density query with filters
        # calculate_density(adapter, node_filter="n.age > 20", edge_filter="r.weight > 0.5")
        
        def query_side_effect(query, params=None):
            if "WHERE n.age > 20" in query and "count(n)" in query:
                return [{'count': 2}] # 2 nodes match filter
            if "WHERE (n.age > 20) AND (m.age > 20) AND (r.weight > 0.5)" in query and "count(r)" in query:
                return [{'count': 1}] # 1 edge matches filter
            return []
            
        adapter.query.side_effect = query_side_effect
        
        density = calculate_density(adapter, node_filter="n.age > 20", edge_filter="r.weight > 0.5")
        # Density = 2 * 1 / (2 * 1) = 1.0
        self.assertEqual(density, 1.0)

if __name__ == '__main__':
    unittest.main()
