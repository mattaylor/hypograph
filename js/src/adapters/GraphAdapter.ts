export interface GraphAdapter {
    connect(uri: string, auth?: any): Promise<void>;
    close(): Promise<void>;
    query(query: string, params?: Record<string, any>): Promise<any[]>;
    getNodes(label?: string): Promise<any[]>;
    getEdges(relationshipType?: string): Promise<any[]>;
}
