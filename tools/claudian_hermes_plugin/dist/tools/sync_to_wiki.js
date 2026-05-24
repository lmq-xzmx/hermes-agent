import { parseFrontMatter } from '../utils/frontmatter.js';
import { shouldSyncByTags, TagFilterMode } from '../utils/tag_filter.js';
import { shouldIncludePath, PathFilterMode } from '../utils/path_filter.js';
import { scanContent, formatScanReport } from '../utils/sensitive_scan.js';
export const syncToWikiTool = {
    name: 'sync_to_wiki',
    description: '同步文件到 LLM Wiki（支持完全共享模式过滤）',
    inputSchema: {
        type: 'object',
        properties: {
            space_id: {
                type: 'string',
                description: '目标 Space ID',
            },
            file_path: {
                type: 'string',
                description: '要同步的文件路径（Obsidian Vault 中的绝对路径）',
            },
            mode: {
                type: 'string',
                enum: ['selective', 'full'],
                description: '同步模式：selective（仅 published） 或 full（完全共享）',
                default: 'selective',
            },
        },
        required: ['space_id', 'file_path'],
    },
};
export async function syncToWikiHandler(args, hermes) {
    const parsed = args;
    try {
        // TODO: 实际读取文件内容并应用过滤
        // 目前是简化版本，实际实现需要读取 Obsidian vault 文件
        const content = ''; // 占位
        const frontMatter = parseFrontMatter(content);
        // 应用标签过滤
        const filterMode = parsed.mode === 'full' ? TagFilterMode.FULL : TagFilterMode.SELECTIVE;
        const tagCheck = shouldSyncByTags(content, filterMode);
        if (!tagCheck.shouldSync) {
            return {
                content: [
                    {
                        type: 'text',
                        text: `⏭️ 文件已跳过同步：\n- 路径: ${parsed.file_path}\n- 原因: ${tagCheck.reason}`,
                    },
                ],
            };
        }
        // 应用路径过滤（raw/ 目录检查）
        if (!shouldIncludePath(parsed.file_path, PathFilterMode.STRICT)) {
            return {
                content: [
                    {
                        type: 'text',
                        text: `⏭️ raw/ 目录文件已跳过：${parsed.file_path}`,
                    },
                ],
            };
        }
        // 敏感内容扫描
        const scanResult = scanContent(content, parsed.file_path);
        if (!scanResult.safe) {
            return {
                content: [
                    {
                        type: 'text',
                        text: `⚠️ 敏感内容检测：\n${formatScanReport(scanResult)}\n\n文件已标记为 personal，不同步到团队。`,
                    },
                ],
                isError: true,
            };
        }
        await hermes.syncToWiki(parsed.space_id, parsed.file_path);
        return {
            content: [
                {
                    type: 'text',
                    text: `✅ 已触发同步：\n- Space: \`${parsed.space_id}\`\n- 文件: ${parsed.file_path}\n- 模式: ${parsed.mode || 'selective'}\n\n请稍后使用 get_sync_status 查看同步状态。`,
                },
            ],
        };
    }
    catch (error) {
        return {
            content: [
                {
                    type: 'text',
                    text: `❌ 同步失败：${error instanceof Error ? error.message : String(error)}`,
                },
            ],
            isError: true,
        };
    }
}
//# sourceMappingURL=sync_to_wiki.js.map