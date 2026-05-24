/**
 * Tag Filter - 根据标签过滤笔记是否应同步
 */
import { parseFrontMatter } from './frontmatter.js';
export var TagFilterMode;
(function (TagFilterMode) {
    TagFilterMode["SELECTIVE"] = "selective";
    TagFilterMode["FULL"] = "full";
})(TagFilterMode || (TagFilterMode = {}));
// 禁止同步的标签
const BLOCKED_TAGS = ['personal', 'draft'];
// 需要明确标记才能同步的标签（选择性模式）
const PUBLISHED_REQUIRED = ['selective'];
/**
 * 检查笔记是否应该同步
 */
export function shouldSyncByTags(content, mode = TagFilterMode.SELECTIVE) {
    const frontMatter = parseFrontMatter(content);
    if (!frontMatter) {
        // 没有 front matter 的笔记
        if (mode === TagFilterMode.FULL) {
            return { shouldSync: true, reason: 'no front matter, full mode', tags: [] };
        }
        return { shouldSync: false, reason: 'no front matter, selective mode requires published', tags: [] };
    }
    const tags = frontMatter.tags || [];
    // 检查是否包含禁止标签
    for (const tag of tags) {
        if (BLOCKED_TAGS.includes(tag)) {
            return {
                shouldSync: false,
                reason: `contains blocked tag: ${tag}`,
                tags,
            };
        }
    }
    // 选择性模式：需要 published 或 completed 状态
    if (mode === TagFilterMode.SELECTIVE) {
        const status = frontMatter.status;
        if (status === 'published' || status === 'completed') {
            return { shouldSync: true, reason: 'status is published/completed', tags };
        }
        // 检查是否包含 published 标签
        if (tags.includes('published')) {
            return { shouldSync: true, reason: 'has published tag', tags };
        }
        return { shouldSync: false, reason: 'selective mode requires published status or tag', tags };
    }
    // 完全共享模式：除了 personal/draft 外都同步
    return { shouldSync: true, reason: 'full share mode allows all non-blocked', tags };
}
/**
 * 过滤笔记列表，返回应该同步的笔记
 */
export function filterByTags(files, mode = TagFilterMode.SELECTIVE) {
    const results = [];
    for (const file of files) {
        const result = shouldSyncByTags(file.content, mode);
        if (result.shouldSync) {
            results.push({ path: file.path, content: file.content, reason: result.reason });
        }
    }
    return results;
}
//# sourceMappingURL=tag_filter.js.map