import type { HermesClient } from '../api/hermes_client.js';
import type { ToolDefinition, ToolResult } from '../types.js';

export const fullSyncStatusTool: ToolDefinition = {
  name: 'full_sync_status',
  description: '查询全量同步任务进度',
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

interface FullSyncStatusArgs {
  task_id: string;
}

export async function fullSyncStatusHandler(
  args: unknown,
  hermes: HermesClient
): Promise<ToolResult> {
  const parsed = args as FullSyncStatusArgs;

  try {
    const status = await hermes.fullSyncStatus(parsed.task_id);

    const statusIcon = status.status === 'completed' ? '✅' :
                        status.status === 'in_progress' ? '🔄' :
                        status.status === 'aborted' ? '🛑' : '⏳';

    const progress = status.total_batches > 0
      ? Math.round((status.completed_batches / status.total_batches) * 100)
      : 0;

    return {
      content: [
        {
          type: 'text',
          text: `${statusIcon} 全量同步状态：

- Task ID: \`${status.task_id}\`
- 状态: ${status.status}
- 进度: ${status.completed_batches}/${status.total_batches} 批次 (${progress}%)
- 已同步: ${status.files_synced} 文件
- 失败: ${status.files_failed} 文件
${status.errors.length > 0 ? `- 错误: ${status.errors.slice(0, 3).join(', ')}` : ''}`,
        },
      ],
    };
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `❌ 查询状态失败：${error instanceof Error ? error.message : String(error)}`,
        },
      ],
      isError: true,
    };
  }
}