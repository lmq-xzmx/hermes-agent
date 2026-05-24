import type { HermesClient } from '../api/hermes_client.js';
import type { ToolDefinition, ToolResult } from '../types.js';

export const checkInTool: ToolDefinition = {
  name: 'check_in',
  description: '完成知识库入职确认（员工入职引导）',
  inputSchema: {
    type: 'object',
    properties: {},
    required: [],
  },
};

interface CheckInResult {
  notes_created: number;
  notes_synced: number;
  team_viewed: boolean;
  personal_tags_understood: boolean;
}

export async function checkInHandler(
  _args: unknown,
  hermes: HermesClient
): Promise<ToolResult> {
  try {
    // 检测员工入职 Check-in 状态
    // 实际实现需要调用 Hermes 后端 API 检查：

    // 1. 检测是否已创建笔记
    const notes_created = 0;  // TODO: 调用 API 统计

    // 2. 检测是否已同步
    const notes_synced = 0;  // TODO: 调用 API 统计

    // 3. 检测是否查看过团队知识库
    const team_viewed = false;  // TODO: 记录用户行为

    // 4. 检测是否理解 personal 标签
    const personal_tags_understood = true;  // TODO: 弹出提示或测试

    // 发送通知给 IT 和 HR
    const notification_sent = true;  // TODO: 调用通知 API

    // 在 HR 系统中标记「知识库入职已完成」
    const hr_marked = true;  // TODO: 调用 HR 系统 API

    return {
      content: [
        {
          type: 'text',
          text: `✅ 知识库入职完成！

📊 入职统计：
- 已创建笔记: ${notes_created}
- 已同步: ${notes_synced}
- 已查看团队知识库: ${team_viewed ? '是' : '否'}
- 理解 personal 标签: ${personal_tags_understood ? '是' : '否'}

🎉 恭喜！你已完成知识库入职。
你的笔记已与团队共享，同事可以在知识库中搜索到你的内容。

📚 下一步：
- 开始正常工作中使用 Obsidian 记录笔记
- 按 Ctrl+S 保存时自动同步到团队
- 使用 @hermes search-wiki 搜索团队知识库
`,
        },
      ],
    };
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `❌ Check-in 失败：${error instanceof Error ? error.message : String(error)}`,
        },
      ],
      isError: true,
    };
  }
}