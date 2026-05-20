export const searchWikiTool = {
    name: 'search_wiki',
    description: '语义搜索 LLM Wiki 知识库',
    inputSchema: {
        type: 'object',
        properties: {
            query: {
                type: 'string',
                description: '搜索query',
            },
            space_id: {
                type: 'string',
                description: 'Space ID（作为 project）',
            },
            limit: {
                type: 'number',
                description: '返回结果数量限制',
                default: 10,
            },
        },
        required: ['query', 'space_id'],
    },
};
export async function searchWikiHandler(args, hermes) {
    const parsed = args;
    try {
        const results = await hermes.searchWiki(parsed.query, parsed.space_id, parsed.limit ?? 10);
        if (results.length === 0) {
            return {
                content: [
                    {
                        type: 'text',
                        text: `没有找到与 "${parsed.query}" 相关的结果。`,
                    },
                ],
            };
        }
        const lines = results.map((r, i) => {
            const highlight = r.highlights?.[0] || r.snippet;
            return `${i + 1}. **${r.title}**\n   ${highlight}${r.path ? `\n   路径: \`${r.path}\`` : ''}`;
        });
        return {
            content: [
                {
                    type: 'text',
                    text: `找到 ${results.length} 个相关结果：\n\n${lines.join('\n\n')}`,
                },
            ],
        };
    }
    catch (error) {
        return {
            content: [
                {
                    type: 'text',
                    text: `❌ 搜索失败：${error instanceof Error ? error.message : String(error)}`,
                },
            ],
            isError: true,
        };
    }
}
//# sourceMappingURL=search_wiki.js.map