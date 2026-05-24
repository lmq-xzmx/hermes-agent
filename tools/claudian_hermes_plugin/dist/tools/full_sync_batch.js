export const fullSyncBatchTool = {
    name: 'full_sync_batch',
    description: '分批次传输文件（用于全量同步）',
    inputSchema: {
        type: 'object',
        properties: {
            task_id: {
                type: 'string',
                description: '同步任务 ID（从 full_sync_start 获取）',
            },
            batch_index: {
                type: 'number',
                description: '批次序号（从 0 开始）',
            },
            files: {
                type: 'array',
                description: '文件列表',
                items: {
                    type: 'object',
                    properties: {
                        path: { type: 'string', description: '文件路径' },
                        checksum: { type: 'string', description: 'SHA256 校验和' },
                        content: { type: 'string', description: '文件内容（可选）' },
                    },
                    required: ['path', 'checksum'],
                },
            },
        },
        required: ['task_id', 'batch_index', 'files'],
    },
};
export async function fullSyncBatchHandler(args, hermes) {
    const parsed = args;
    try {
        const result = await hermes.fullSyncBatch(parsed.task_id, parsed.batch_index, parsed.files);
        return {
            content: [
                {
                    type: 'text',
                    text: `📦 批次 ${parsed.batch_index} 完成：\n- 成功: ${result.completed}\n- 失败: ${result.failed}\n- Task ID: \`${parsed.task_id}\``,
                },
            ],
        };
    }
    catch (error) {
        return {
            content: [
                {
                    type: 'text',
                    text: `❌ 批次传输失败：${error instanceof Error ? error.message : String(error)}`,
                },
            ],
            isError: true,
        };
    }
}
//# sourceMappingURL=full_sync_batch.js.map