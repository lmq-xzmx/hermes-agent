import type { HermesClient } from '../api/hermes_client.js';
import type { ToolDefinition, ToolResult } from '../types.js';

export const fullSyncAbortTool: ToolDefinition = {
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

interface FullSyncAbortArgs {
  task_id: string;
}

export async function fullSyncAbortHandler(
  args: unknown,
  hermes: HermesClient
): Promise<ToolResult> {
  const parsed = args as FullSyncAbortArgs;

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
  } catch (error) {
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