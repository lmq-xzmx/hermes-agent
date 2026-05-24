export const fullSyncAbortTool = {
    name: 'full_sync_abort',
    description: '中止全量同步任务',
    inputSchema: {
        type: 'object',
        properties: {
            task_id: {
                type: 'string',
                description: '同步任务 ID',
            },
        },
        required: ['task_id'],
    },
};
export async function fullSyncAbortHandler(args, hermes) {
    const parsed = args;
    try {
        const result = await hermes.fullSyncAbort(parsed.task_id);
        return {
            content: [
                {
                    type: 'text',
                    text: `🛑 全量同步已中止：\n- Task ID: \`${parsed.task_id}\`\n- 消息: ${result.message}`,
                },
            ],
        };
    }
    catch (error) {
        return {
            content: [
                {
                    type: 'text',
                    text: `❌ 中止失败：${error instanceof Error ? error.message : String(error)}`,
                },
            ],
            isError: true,
        };
    }
}
//# sourceMappingURL=full_sync_abort.js.map