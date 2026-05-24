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
    fullSyncStart(spaceId: string, options?: {
        include_raw?: boolean;
        transition_days?: number;
    }): Promise<{
        task_id: string;
        total_files: number;
    }>;
    fullSyncBatch(taskId: string, batchIndex: number, files: Array<{
        path: string;
        checksum: string;
        content?: string;
    }>): Promise<{
        completed: number;
        failed: number;
    }>;
    fullSyncGraph(taskId: string, entities: unknown[], relations: unknown[]): Promise<{
        entities_synced: number;
        relations_synced: number;
    }>;
    fullSyncStatus(taskId: string): Promise<{
        task_id: string;
        status: 'pending' | 'in_progress' | 'completed' | 'aborted';
        total_batches: number;
        completed_batches: number;
        files_synced: number;
        files_failed: number;
        errors: string[];
    }>;
    fullSyncAbort(taskId: string): Promise<{
        aborted: boolean;
        message: string;
    }>;
}
//# sourceMappingURL=hermes_client.d.ts.map