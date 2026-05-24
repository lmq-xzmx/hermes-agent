export const fullSyncGraphTool = {
    name: 'full_sync_graph',
    description: '传输图谱结构（实体/概念/关系）',
    inputSchema: {
        type: 'object',
        properties: {
            task_id: {
                type: 'string',
                description: '同步任务 ID',
            },
            entities: {
                type: 'array',
                description: '实体列表',
                items: {
                    type: 'object',
                    properties: {
                        id: { type: 'string', description: '实体 ID' },
                        type: { type: 'string', description: '实体类型（person/project/technology）' },
                        name: { type: 'string', description: '实体名称' },
                        page_path: { type: 'string', description: '来源页面路径' },
                    },
                    required: ['id', 'type', 'name'],
                },
            },
            relations: {
                type: 'array',
                description: '关系列表',
                items: {
                    type: 'object',
                    properties: {
                        source_id: { type: 'string', description: '源实体 ID' },
                        target_id: { type: 'string', description: '目标实体 ID' },
                        relation_type: { type: 'string', description: '关系类型' },
                        weight: { type: 'number', description: '权重（0-1）' },
                    },
                    required: ['source_id', 'target_id', 'relation_type'],
                },
            },
        },
        required: ['task_id', 'entities', 'relations'],
    },
};
export async function fullSyncGraphHandler(args, hermes) {
    const parsed = args;
    try {
        const result = await hermes.fullSyncGraph(parsed.task_id, parsed.entities, parsed.relations);
        return {
            content: [
                {
                    type: 'text',
                    text: `🕸️ 图谱同步完成：\n- 实体: ${result.entities_synced}\n- 关系: ${result.relations_synced}\n- Task ID: \`${parsed.task_id}\``,
                },
            ],
        };
    }
    catch (error) {
        return {
            content: [
                {
                    type: 'text',
                    text: `❌ 图谱同步失败：${error instanceof Error ? error.message : String(error)}`,
                },
            ],
            isError: true,
        };
    }
}
//# sourceMappingURL=full_sync_graph.js.map