import type { HermesClient } from '../api/hermes_client.js';
import type { ToolDefinition, ToolResult } from '../types.js';

export const syncToWikiTool: ToolDefinition = {
  name: 'sync_to_wiki',
  description: '同步文件到 LLM Wiki',
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
    },
    required: ['space_id', 'file_path'],
  },
};

interface SyncToWikiArgs {
  space_id: string;
  file_path: string;
}

export async function syncToWikiHandler(
  args: unknown,
  hermes: HermesClient
): Promise<ToolResult> {
  const parsed = args as SyncToWikiArgs;

  try {
    await hermes.syncToWiki(parsed.space_id, parsed.file_path);

    return {
      content: [
        {
          type: 'text',
          text: `✅ 已触发同步：\n- Space: \`${parsed.space_id}\`\n- 文件: ${parsed.file_path}\n\n请稍后使用 get_sync_status 查看同步状态。`,
        },
      ],
    };
  } catch (error) {
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