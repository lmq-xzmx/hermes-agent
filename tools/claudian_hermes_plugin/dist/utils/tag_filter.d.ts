/**
 * Tag Filter - 根据标签过滤笔记是否应同步
 */
export declare enum TagFilterMode {
    SELECTIVE = "selective",// 仅同步 published 标签
    FULL = "full"
}
export interface TagFilterResult {
    shouldSync: boolean;
    reason: string;
    tags: string[];
}
/**
 * 检查笔记是否应该同步
 */
export declare function shouldSyncByTags(content: string, mode?: TagFilterMode): TagFilterResult;
/**
 * 过滤笔记列表，返回应该同步的笔记
 */
export declare function filterByTags(files: Array<{
    path: string;
    content: string;
}>, mode?: TagFilterMode): Array<{
    path: string;
    content: string;
    reason: string;
}>;
//# sourceMappingURL=tag_filter.d.ts.map