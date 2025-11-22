import * as fs from 'fs';
import * as readline from 'readline';
import { GraphAdapter } from './adapters/GraphAdapter';

export class CSVImporter {
    private adapter: GraphAdapter;

    constructor(adapter: GraphAdapter) {
        this.adapter = adapter;
    }

    async importNodes(csvPath: string, label: string, idCol: string = "id", propertyCols?: string[]): Promise<void> {
        const fileStream = fs.createReadStream(csvPath);
        const rl = readline.createInterface({
            input: fileStream,
            crlfDelay: Infinity
        });

        let headers: string[] = [];
        let isFirstLine = true;

        for await (const line of rl) {
            if (isFirstLine) {
                headers = line.split(',');
                isFirstLine = false;
                continue;
            }

            const values = line.split(',');
            const row: Record<string, any> = {};
            headers.forEach((h, i) => {
                row[h.trim()] = values[i]?.trim();
            });

            const props: Record<string, any> = {};
            if (propertyCols) {
                propertyCols.forEach(col => {
                    if (row[col] !== undefined) {
                        props[col] = row[col];
                    }
                });
            } else {
                Object.keys(row).forEach(k => {
                    if (k !== idCol) {
                        props[k] = row[k];
                    }
                });
            }

            const query = `MERGE (n:${label} { ${idCol}: $idVal }) SET n += $props`;
            await this.adapter.query(query, { idVal: row[idCol], props });
        }
    }

    async importEdges(
        csvPath: string, 
        sourceCol: string, 
        targetCol: string, 
        relationshipType: string,
        sourceLabel: string,
        targetLabel: string,
        sourceIdCol: string = "id",
        targetIdCol: string = "id",
        weightCol?: string,
        propertyCols?: string[]
    ): Promise<void> {
        const fileStream = fs.createReadStream(csvPath);
        const rl = readline.createInterface({
            input: fileStream,
            crlfDelay: Infinity
        });

        let headers: string[] = [];
        let isFirstLine = true;

        for await (const line of rl) {
            if (isFirstLine) {
                headers = line.split(',');
                isFirstLine = false;
                continue;
            }

            const values = line.split(',');
            const row: Record<string, any> = {};
            headers.forEach((h, i) => {
                row[h.trim()] = values[i]?.trim();
            });

            const props: Record<string, any> = {};
            if (weightCol && row[weightCol] !== undefined) {
                props[weightCol] = parseFloat(row[weightCol]) || 0.0;
            }

            if (propertyCols) {
                propertyCols.forEach(col => {
                    if (col !== weightCol && row[col] !== undefined) {
                        props[col] = row[col];
                    }
                });
            }

            const query = `
            MATCH (a:${sourceLabel} { ${sourceIdCol}: $sourceId })
            MATCH (b:${targetLabel} { ${targetIdCol}: $targetId })
            MERGE (a)-[r:${relationshipType}]->(b)
            SET r += $props
            `;

            await this.adapter.query(query, {
                sourceId: row[sourceCol],
                targetId: row[targetCol],
                props
            });
        }
    }
}
