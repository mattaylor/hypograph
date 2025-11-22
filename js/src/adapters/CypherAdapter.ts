import neo4j, { Driver, Session } from 'neo4j-driver';
import { GraphAdapter } from './GraphAdapter';

export class CypherAdapter implements GraphAdapter {
    private driver: Driver | null = null;

    async connect(uri: string, user?: string, password?: string): Promise<void> {
        const auth = (user && password) ? neo4j.auth.basic(user, password) : undefined;
        this.driver = neo4j.driver(uri, auth);
    }

    async close(): Promise<void> {
        if (this.driver) {
            await this.driver.close();
        }
    }

    async query(query: string, params?: Record<string, any>): Promise<any[]> {
        if (!this.driver) {
            throw new Error("Not connected to the database.");
        }

        const session: Session = this.driver.session();
        try {
            const result = await session.run(query, params);
            return result.records.map(record => record.toObject());
        } finally {
            await session.close();
        }
    }

    async getNodes(label?: string): Promise<any[]> {
        let query = "MATCH (n) RETURN n";
        if (label) {
            query = `MATCH (n:${label}) RETURN n`;
        }
        return this.query(query);
    }

    async getEdges(relationshipType?: string): Promise<any[]> {
        let query = "MATCH ()-[r]->() RETURN r";
        if (relationshipType) {
            query = `MATCH ()-[r:${relationshipType}]->() RETURN r`;
        }
        return this.query(query);
    }
}
