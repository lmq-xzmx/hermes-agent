import { z } from 'zod';
export declare const SpaceSchema: z.ZodObject<{
    id: z.ZodString;
    name: z.ZodString;
    team_id: z.ZodOptional<z.ZodString>;
    owner_id: z.ZodString;
    quota_bytes: z.ZodOptional<z.ZodNumber>;
    used_bytes: z.ZodOptional<z.ZodNumber>;
    created_at: z.ZodOptional<z.ZodString>;
    updated_at: z.ZodOptional<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    id: string;
    name: string;
    owner_id: string;
    team_id?: string | undefined;
    quota_bytes?: number | undefined;
    used_bytes?: number | undefined;
    created_at?: string | undefined;
    updated_at?: string | undefined;
}, {
    id: string;
    name: string;
    owner_id: string;
    team_id?: string | undefined;
    quota_bytes?: number | undefined;
    used_bytes?: number | undefined;
    created_at?: string | undefined;
    updated_at?: string | undefined;
}>;
export type Space = z.infer<typeof SpaceSchema>;
export declare const SyncStatusSchema: z.ZodObject<{
    space_id: z.ZodString;
    last_sync: z.ZodNullable<z.ZodString>;
    pending_files: z.ZodOptional<z.ZodNumber>;
    status: z.ZodEnum<["idle", "syncing", "error"]>;
    error_message: z.ZodOptional<z.ZodNullable<z.ZodString>>;
}, "strip", z.ZodTypeAny, {
    status: "idle" | "syncing" | "error";
    space_id: string;
    last_sync: string | null;
    pending_files?: number | undefined;
    error_message?: string | null | undefined;
}, {
    status: "idle" | "syncing" | "error";
    space_id: string;
    last_sync: string | null;
    pending_files?: number | undefined;
    error_message?: string | null | undefined;
}>;
export type SyncStatus = z.infer<typeof SyncStatusSchema>;
export declare const SearchResultSchema: z.ZodObject<{
    id: z.ZodString;
    title: z.ZodString;
    snippet: z.ZodString;
    path: z.ZodOptional<z.ZodString>;
    score: z.ZodOptional<z.ZodNumber>;
    highlights: z.ZodOptional<z.ZodArray<z.ZodString, "many">>;
}, "strip", z.ZodTypeAny, {
    id: string;
    title: string;
    snippet: string;
    path?: string | undefined;
    score?: number | undefined;
    highlights?: string[] | undefined;
}, {
    id: string;
    title: string;
    snippet: string;
    path?: string | undefined;
    score?: number | undefined;
    highlights?: string[] | undefined;
}>;
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
//# sourceMappingURL=types.d.ts.map