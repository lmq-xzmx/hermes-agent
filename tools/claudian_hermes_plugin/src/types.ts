import { z } from 'zod';

export const SpaceSchema = z.object({
  id: z.string(),
  name: z.string(),
  team_id: z.string().optional(),
  owner_id: z.string(),
  quota_bytes: z.number().optional(),
  used_bytes: z.number().optional(),
  created_at: z.string().optional(),
  updated_at: z.string().optional(),
});

export type Space = z.infer<typeof SpaceSchema>;

export const SyncStatusSchema = z.object({
  space_id: z.string(),
  last_sync: z.string().nullable(),
  pending_files: z.number().optional(),
  status: z.enum(['idle', 'syncing', 'error']),
  error_message: z.string().nullable().optional(),
});

export type SyncStatus = z.infer<typeof SyncStatusSchema>;

export const SearchResultSchema = z.object({
  id: z.string(),
  title: z.string(),
  snippet: z.string(),
  path: z.string().optional(),
  score: z.number().optional(),
  highlights: z.array(z.string()).optional(),
});

export type SearchResult = z.infer<typeof SearchResultSchema>;

export interface HermesConfig {
  hermes: {
    base_url: string;
    token: string;
  };
  mcp: {
    transport: 'stdio' | 'sse' | 'http';
  };
}

export interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: {
    type: 'object';
    properties: Record<string, unknown>;
    required?: string[];
  };
}

export interface ToolResult {
  content: Array<{
    type: 'text';
    text: string;
  }>;
  isError?: boolean;
}