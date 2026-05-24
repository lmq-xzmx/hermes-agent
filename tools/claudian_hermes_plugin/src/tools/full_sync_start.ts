import type { HermesClient } from '../api/hermes_client.js';
import type { ToolDefinition, ToolResult } from '../types.js';

export const fullSyncStartTool: ToolDefinition = {
  name: 'full_sync_start',
  description: '初始化全量同步任务（完全共享模式）',
  inputSchema: {
    type: 'object',
    properties: {
      space_id: {
        type: 'string',
        description: '目标 Space ID',
      },
      include_raw: {
        type: 'boolean',
        description: '是否包含 raw/ 目录（默认 false）',
        default: false,
      },
      transition_days: {
        type: 'number',
        description: '过渡期天数，期间仅 admin 可见（默认 30）',
        default: 30,
      },
    },
    required: ['space_id'],
  },
};

interface FullSyncStartArgs {
  space_id: string;
  include_raw?: boolean;
  transition_days?: number;
}

export async function fullSyncStartHandler(
  args: unknown,
  hermes: HermesClient
): Promise<ToolResult> {
  const parsed = args as FullSyncStartArgs;

  try {
    const result = await hermes.fullSyncStart(parsed.space_id, {
      include_raw: parsed.include_raw,
      transition_days: parsed.transition_days,
    });

    return {
      content: [
        {
          type: 'text',
          text: `🚀 全量同步任务已启动：\n- Task ID: \`${result.task_id}\`\n- 待同步文件: ${result.total_files}\n- 过渡期: ${parsed.transition_days || 30} 天\n\n使用 \`full_sync_status\` 查看进度，\`full_sync_abort\` 可中止。`,
        },
      ],
    };
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `❌ 启动全量同步失败：${error instanceof Error ? error.message : String(error)}`,
        },
      ],
      isError: true,
    };
  }
}