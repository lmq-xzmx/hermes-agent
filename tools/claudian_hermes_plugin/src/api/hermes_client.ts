import { SpaceSchema, SyncStatusSchema, SearchResultSchema, type Space, type SyncStatus, type SearchResult } from '../types.js';

export class HermesClient {
  constructor(
    private baseUrl: string,
    private token: string
  ) {}

  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
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

    return response.json() as Promise<T>;
  }

  async listSpaces(): Promise<Space[]> {
    const result = await this.request<{ spaces: unknown[] }>('/api/v1/spaces');
    return SpaceSchema.array().parse(result.spaces);
  }

  async getSpace(spaceId: string): Promise<Space> {
    const result = await this.request<unknown>(`/api/v1/spaces/${spaceId}`);
    return SpaceSchema.parse(result);
  }

  async syncToWiki(spaceId: string, filePath: string): Promise<void> {
    // 使用 knowledge/sync 端点
    await this.request('/api/v1/knowledge/sync', {
      method: 'POST',
      body: JSON.stringify({
        space_id: spaceId,
        source_path: filePath,
      }),
    });
  }

  async getSyncStatus(spaceId: string): Promise<SyncStatus> {
    // 优先使用 knowledge/sync/status
    try {
      const result = await this.request<unknown>(`/api/v1/knowledge/sync/status?space_id=${spaceId}`);
      return SyncStatusSchema.parse(result);
    } catch {
      // 降级到 space quota 端点
      const result = await this.request<unknown>(`/api/v1/spaces/${spaceId}/quota`);
      return {
        space_id: spaceId,
        last_sync: null,
        status: 'idle',
        ...result as object,
      } as SyncStatus;
    }
  }

  async searchWiki(query: string, spaceId: string, limit = 10): Promise<SearchResult[]> {
    const result = await this.request<{ results: unknown[] }>(
      `/api/v1/knowledge/search?query=${encodeURIComponent(query)}&project=${encodeURIComponent(spaceId)}&limit=${limit}`
    );
    return SearchResultSchema.array().parse(result.results);
  }

  async getKnowledgeSuggestions(query: string, spaceId: string): Promise<string[]> {
    const result = await this.request<{ suggestions: string[] }>(
      `/api/v1/knowledge/suggestions?query=${encodeURIComponent(query)}&project=${encodeURIComponent(spaceId)}`
    );
    return result.suggestions;
  }

  async triggerSync(spaceId: string, filePath?: string): Promise<{ message: string; job_id?: string }> {
    // 触发 delta 同步
    const body: Record<string, unknown> = { space_id: spaceId };
    if (filePath) {
      body.file_path = filePath;
    }

    try {
      // 尝试 sync/delta 端点（如果存在）
      const result = await this.request<{ message?: string; delta?: unknown }>('/api/v1/spaces/{space_id}/sync/delta'.replace('{space_id}', spaceId), {
        method: 'POST',
        body: JSON.stringify(body),
      });
      return { message: result.message || 'Sync triggered', job_id: undefined };
    } catch {
      // 降级到 knowledge sync
      await this.syncToWiki(spaceId, filePath || '');
      return { message: 'Sync triggered via knowledge API' };
    }
  }
}