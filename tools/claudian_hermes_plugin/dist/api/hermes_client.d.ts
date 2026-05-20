import { type Space, type SyncStatus, type SearchResult } from '../types.js';
export declare class HermesClient {
    private baseUrl;
    private token;
    constructor(baseUrl: string, token: string);
    private request;
    listSpaces(): Promise<Space[]>;
    getSpace(spaceId: string): Promise<Space>;
    syncToWiki(spaceId: string, filePath: string): Promise<void>;
    getSyncStatus(spaceId: string): Promise<SyncStatus>;
    searchWiki(query: string, spaceId: string, limit?: number): Promise<SearchResult[]>;
    getKnowledgeSuggestions(query: string, spaceId: string): Promise<string[]>;
    triggerSync(spaceId: string, filePath?: string): Promise<{
        message: string;
        job_id?: string;
    }>;
}
//# sourceMappingURL=hermes_client.d.ts.map