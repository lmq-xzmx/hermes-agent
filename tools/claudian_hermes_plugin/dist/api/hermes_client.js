import { SpaceSchema, SyncStatusSchema, SearchResultSchema } from '../types.js';
export class HermesClient {
    baseUrl;
    token;
    constructor(baseUrl, token) {
        this.baseUrl = baseUrl;
        this.token = token;
    }
    async request(path, options = {}) {
        const url = `${this.baseUrl}${path}`;
        const response = await fetch(url, {
            ...options,
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });
        if (!response.ok) {
            const errorBody = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorBody || response.statusText}`);
        }
        return response.json();
    }
    async listSpaces() {
        const result = await this.request('/api/v1/spaces');
        return SpaceSchema.array().parse(result.spaces);
    }
    async getSpace(spaceId) {
        const result = await this.request(`/api/v1/spaces/${spaceId}`);
        return SpaceSchema.parse(result);
    }
    async syncToWiki(spaceId, filePath) {
        // 使用 knowledge/sync 端点
        await this.request('/api/v1/knowledge/sync', {
            method: 'POST',
            body: JSON.stringify({
                space_id: spaceId,
                source_path: filePath,
            }),
        });
    }
    async getSyncStatus(spaceId) {
        // 优先使用 knowledge/sync/status
        try {
            const result = await this.request(`/api/v1/knowledge/sync/status?space_id=${spaceId}`);
            return SyncStatusSchema.parse(result);
        }
        catch {
            // 降级到 space quota 端点
            const result = await this.request(`/api/v1/spaces/${spaceId}/quota`);
            return {
                space_id: spaceId,
                last_sync: null,
                status: 'idle',
                ...result,
            };
        }
    }
    async searchWiki(query, spaceId, limit = 10) {
        const result = await this.request(`/api/v1/knowledge/search?query=${encodeURIComponent(query)}&project=${encodeURIComponent(spaceId)}&limit=${limit}`);
        return SearchResultSchema.array().parse(result.results);
    }
    async getKnowledgeSuggestions(query, spaceId) {
        const result = await this.request(`/api/v1/knowledge/suggestions?query=${encodeURIComponent(query)}&project=${encodeURIComponent(spaceId)}`);
        return result.suggestions;
    }
    async triggerSync(spaceId, filePath) {
        // 触发 delta 同步
        const body = { space_id: spaceId };
        if (filePath) {
            body.file_path = filePath;
        }
        try {
            // 尝试 sync/delta 端点（如果存在）
            const result = await this.request('/api/v1/spaces/{space_id}/sync/delta'.replace('{space_id}', spaceId), {
                method: 'POST',
                body: JSON.stringify(body),
            });
            return { message: result.message || 'Sync triggered', job_id: undefined };
        }
        catch {
            // 降级到 knowledge sync
            await this.syncToWiki(spaceId, filePath || '');
            return { message: 'Sync triggered via knowledge API' };
        }
    }
    // ========== Full Sync APIs ==========
    async fullSyncStart(spaceId, options) {
        const body = { space_id: spaceId };
        if (options) {
            if (options.include_raw !== undefined)
                body.include_raw = options.include_raw;
            if (options.transition_days !== undefined)
                body.transition_days = options.transition_days;
        }
        const result = await this.request('/api/v1/knowledge/sync/full/start', { method: 'POST', body: JSON.stringify(body) });
        return result;
    }
    async fullSyncBatch(taskId, batchIndex, files) {
        const result = await this.request('/api/v1/knowledge/sync/full/batch', {
            method: 'POST',
            body: JSON.stringify({ task_id: taskId, batch_index: batchIndex, files }),
        });
        return result;
    }
    async fullSyncGraph(taskId, entities, relations) {
        const result = await this.request('/api/v1/knowledge/sync/full/graph', {
            method: 'POST',
            body: JSON.stringify({ task_id: taskId, entities, relations }),
        });
        return result;
    }
    async fullSyncStatus(taskId) {
        return this.request(`/api/v1/knowledge/sync/full/${taskId}`, { method: 'GET' });
    }
    async fullSyncAbort(taskId) {
        return this.request(`/api/v1/knowledge/sync/full/${taskId}/abort`, { method: 'POST' });
    }
}
//# sourceMappingURL=hermes_client.js.map