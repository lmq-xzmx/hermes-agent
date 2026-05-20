import type { HermesClient } from '../api/hermes_client.js';
import type { ToolDefinition, ToolResult } from '../types.js';

export const getSyncStatusTool: ToolDefinition = {
  name: 'get_sync_status',
  description: '获取同步状态',
  inputSchema: {
    type: 'object',
    properties: {
      space_id: {
        type: 'string',
        description: 'Space ID',
      },
    },
    required: ['space_id'],
  },
};

interface GetSyncStatusArgs {
  space_id: string;
}

export async function getSyncStatusHandler(
  args: unknown,
  hermes: HermesClient
): Promise<ToolResult> {
  const parsed = args as GetSyncStatusArgs;

  try {
    const status = await hermes.getSyncStatus(parsed.space_id);

    const statusIcon = status.status === 'idle' ? '✅' : status.status === 'syncing' ? '🔄' : '❌';
    const lastSync = status.last_sync
      ? new Date(status.last_sync).toLocaleString()
      : '从未同步';

    return {
      content: [
        {
          type: 'text',
          text: `${statusIcon} 同步状态：\n- Space: \`${status.space_id}\`\n- 状态: ${status.status}\n- 最后同步: ${lastSync}${status.pending_files ? `\n- 待同步文件: ${status.pending_files}` : ''}${status.error_message ? `\n- 错误: ${status.error_message}` : ''}`,
        },
      ],
    };
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `❌ 获取状态失败：${error instanceof Error ? error.message : String(error)}`,
        },
      ],
      isError: true,
    };
  }
}