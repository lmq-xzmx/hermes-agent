import type { HermesClient } from '../api/hermes_client.js';
import type { ToolDefinition, ToolResult } from '../types.js';

export const listSpacesTool: ToolDefinition = {
  name: 'list_spaces',
  description: '列出用户可访问的所有 Space',
  inputSchema: {
    type: 'object',
    properties: {},
    required: [],
  },
};

export async function listSpacesHandler(
  _args: unknown,
  hermes: HermesClient
): Promise<ToolResult> {
  try {
    const spaces = await hermes.listSpaces();

    if (spaces.length === 0) {
      return {
        content: [
          {
            type: 'text',
            text: '没有找到可访问的 Space。请先在 Hermes File Manager 中创建 Space。',
          },
        ],
      };
    }

    const lines = spaces.map(
      (s, i) => `${i + 1}. **${s.name}** (ID: \`${s.id}\`)`
    );

    return {
      content: [
        {
          type: 'text',
          text: `共 ${spaces.length} 个 Space：\n\n${lines.join('\n')}`,
        },
      ],
    };
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `获取 Space 列表失败：${error instanceof Error ? error.message : String(error)}`,
        },
      ],
      isError: true,
    };
  }
}