import { CypherAdapter } from '../../js/src/adapters/CypherAdapter';
import { CSVImporter } from '../../js/src/importer';
import { calculateDensity } from '../../js/src/stats/inference';
import { degreeCentrality } from '../../js/src/stats/centrality';
import { anovaTest, correlationTest } from '../../js/src/stats/hypothesis';

async function main() {
    const uri = process.env.DB_URI || "bolt://localhost:7687";
    const user = process.env.DB_USER || "neo4j";
    const password = process.env.DB_PASS || "password";

    const adapter = new CypherAdapter();
    
    try {
        await adapter.connect(uri, user, password);
        console.log("Connected to database.");

        // 1. Import Healthcare Data
        console.log("\n--- Importing Healthcare Data ---");
        const importer = new CSVImporter(adapter);
        
        // Note: Paths are relative to where the script is run. Adjust as needed.
        await importer.importNodes("../../data/healthcare/patients.csv", "Patient");
        await importer.importNodes("../../data/healthcare/conditions.csv", "Condition");
        await importer.importNodes("../../data/healthcare/treatments.csv", "Treatment");
        
        // importEdges(csvPath, sourceCol, targetCol, relType, sourceLabel, targetLabel, ...)
        await importer.importEdges(
            "../../data/healthcare/patient_condition_edges.csv", 
            "source", "target", "HAS_CONDITION", "Patient", "Condition"
        );
        
        await importer.importEdges(
            "../../data/healthcare/patient_treatment_edges.csv", 
            "source", "target", "UNDERWENT", "Patient", "Treatment",
            "id", "id", "outcome_score"
        );
        
        console.log("Data import complete.");

        // 2. Basic Inference
        console.log("\n--- Basic Graph Stats ---");
        const density = await calculateDensity(adapter);
        console.log(`Graph Density: ${density.toFixed(4)}`);

        // 3. Subgraph Analysis (Cohort: Patients > 60)
        console.log("\n--- Subgraph Analysis (Patients > 60) ---");
        const cohortFilter = "(n:Patient AND toInteger(n.age) > 60) OR n:Condition OR n:Treatment";
        const cohortDensity = await calculateDensity(adapter, undefined, cohortFilter);
        console.log(`Cohort Density (Patients > 60): ${cohortDensity.toFixed(4)}`);

        // 4. Centrality (Identifying Key Conditions)
        console.log("\n--- Condition Centrality (Prevalence) ---");
        const centrality = await degreeCentrality(adapter, "IN");
        
        // Fetch condition names
        const conditions = await adapter.query("MATCH (c:Condition) RETURN id(c) as id, c.name as name");
        const condMap = new Map<string, string>();
        conditions.forEach(row => condMap.set(String(row.id), String(row.name)));
        
        console.log("Top Conditions by Patient Count:");
        Object.entries(centrality)
            .sort(([, a], [, b]) => b - a)
            .forEach(([id, score]) => {
                if (condMap.has(id)) {
                    console.log(`  ${condMap.get(id)}: ${score.toFixed(4)}`);
                }
            });

        // 5. Hypothesis Testing
        console.log("\n--- Hypothesis Testing ---");
        
        // Correlation: Age vs Recovery Score
        const { correlation, pValue: pCorr } = await correlationTest(adapter, "age", "recovery_score", "n:Patient");
        console.log(`Correlation (Age vs Recovery): r=${correlation.toFixed(4)}, p=${pCorr.toFixed(4)}`);
        
        // ANOVA: Recovery Score by Gender
        const { fStat, pValue: pAnova } = await anovaTest(adapter, "gender", "recovery_score", "n:Patient");
        console.log(`ANOVA (Recovery by Gender): F=${fStat.toFixed(4)}, p=${pAnova.toFixed(4)}`);

    } catch (error) {
        console.error("Error:", error);
    } finally {
        await adapter.close();
    }
}

main().catch(console.error);
