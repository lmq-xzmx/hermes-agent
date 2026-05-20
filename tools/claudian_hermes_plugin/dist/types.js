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
export const SyncStatusSchema = z.object({
    space_id: z.string(),
    last_sync: z.string().nullable(),
    pending_files: z.number().optional(),
    status: z.enum(['idle', 'syncing', 'error']),
    error_message: z.string().nullable().optional(),
});
export const SearchResultSchema = z.object({
    id: z.string(),
    title: z.string(),
    snippet: z.string(),
    path: z.string().optional(),
    score: z.number().optional(),
    highlights: z.array(z.string()).optional(),
});
//# sourceMappingURL=types.js.map