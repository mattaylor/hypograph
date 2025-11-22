import os
from hypograph.adapters.cypher_adapter import CypherAdapter
from hypograph.stats.inference import calculate_density, get_degree_distribution
from hypograph.stats.centrality import degree_centrality, pagerank
from hypograph.stats.advanced_hypothesis import anova_test, correlation_test
from hypograph.importer import CSVImporter

def main():
    # Initialize Adapter
    uri = os.getenv("DB_URI", "bolt://localhost:7687")
    user = os.getenv("DB_USER", "neo4j")
    password = os.getenv("DB_PASS", "password")
    
    try:
        adapter = CypherAdapter(uri, user, password)
        print("Connected to database.")
        
        # 1. Import Healthcare Data
        print("\n--- Importing Healthcare Data ---")
        importer = CSVImporter(adapter)
        
        # Import Nodes
        importer.import_nodes("../../data/healthcare/patients.csv", "Patient")
        importer.import_nodes("../../data/healthcare/conditions.csv", "Condition")
        importer.import_nodes("../../data/healthcare/treatments.csv", "Treatment")
        
        # Import Edges
        importer.import_edges("../../data/healthcare/patient_condition_edges.csv", "HAS_CONDITION", weight_col=None)
        importer.import_edges("../../data/healthcare/patient_treatment_edges.csv", "UNDERWENT", weight_col="outcome_score")
        
        print("Data import complete.")
        
        # 2. Basic Inference
        print("\n--- Basic Graph Stats ---")
        density = calculate_density(adapter)
        print(f"Graph Density: {density:.4f}")
        
        # 3. Subgraph Analysis (Cohort: Patients > 60)
        print("\n--- Subgraph Analysis (Patients > 60) ---")
        # Filter: Nodes must be Patients > 60 OR Conditions/Treatments connected to them
        # Note: Simple node filter "n.age > 60" might exclude non-patient nodes if they don't have age property.
        # Better filter: "(n:Patient AND n.age > 60) OR n:Condition OR n:Treatment"
        cohort_filter = "(n:Patient AND toInteger(n.age) > 60) OR n:Condition OR n:Treatment"
        
        cohort_density = calculate_density(adapter, node_filter=cohort_filter)
        print(f"Cohort Density (Patients > 60): {cohort_density:.4f}")
        
        # 4. Centrality (Identifying Key Conditions)
        print("\n--- Condition Centrality (Prevalence) ---")
        # We want degree centrality of Conditions (in-degree from Patients)
        # Filter: Only consider Condition nodes and HAS_CONDITION edges?
        # degree_centrality calculates for ALL nodes matching filter.
        # Let's calculate for all and filter output.
        centrality = degree_centrality(adapter, direction="IN")
        
        # Fetch condition names to map IDs
        conditions = adapter.query("MATCH (c:Condition) RETURN id(c) as id, c.name as name")
        cond_map = {str(row['id']): row['name'] for row in conditions}
        
        print("Top Conditions by Patient Count:")
        sorted_centrality = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        for node_id, score in sorted_centrality:
            if node_id in cond_map:
                print(f"  {cond_map[node_id]}: {score:.4f}")

        # 5. Hypothesis Testing
        print("\n--- Hypothesis Testing ---")
        
        # Correlation: Age vs Recovery Score
        # Both are properties of Patient nodes
        corr, p_val = correlation_test(adapter, "age", "recovery_score", node_filter="n:Patient")
        print(f"Correlation (Age vs Recovery): r={corr:.4f}, p={p_val:.4f}")
        
        # ANOVA: Recovery Score by Gender
        f_stat, p_val_anova = anova_test(adapter, "gender", "recovery_score", node_filter="n:Patient")
        print(f"ANOVA (Recovery by Gender): F={f_stat:.4f}, p={p_val_anova:.4f}")

        adapter.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
