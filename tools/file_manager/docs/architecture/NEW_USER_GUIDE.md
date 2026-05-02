# 普通用户新手指导

## 领域分类

**领域**：企业级文件管理 / 云存储协作平台 (Enterprise File Management & Cloud Storage Collaboration Platform)

**子领域**：
- 多租户存储资源管理 (Multi-tenant Storage Resource Management)
- 基于事件的引导系统 (Event-driven Guidance System)
- 工作流与知识协作 (Workflow & Knowledge Collaboration)

---

## 新手引导体系设计

### 核心原则

1. **基于事件驱动**：不在用户首次访问时弹出大量教程，而是在关键操作节点提供适时帮助
2. **渐进式学习**：从"能干活"到"用得好"分阶段引导
3. **行动导向**：每个引导都指向具体操作，而非抽象概念
4. **容错设计**：允许用户犯错，通过引导纠正而非阻止

---

## 用户旅程引导地图

```
┌─────────────────────────────────────────────────────────────────┐
│                    新用户成长旅程                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  【阶段1】入门                                                   │
│  注册 → 加入团队 → 上传第一个文件                               │
│  │                                                              │
│  ▼                                                              │
│  【阶段2】协作                                                   │
│  分享文件 → 邀请成员 → 使用工作流                               │
│  │                                                              │
│  ▼                                                              │
│  【阶段3】进阶                                                   │
│  版本历史 → 私有空间 → 跨团队协作                               │
│  │                                                              │
│  ▼                                                              │
│  【阶段4】专家                                                   │
│  自定义工作流 → 笔记关联 → 数据分析                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 事件驱动引导实现

### 引导事件定义

```javascript
const GUIDANCE_EVENTS = {
    // 阶段1: 入门
    "USER_REGISTERED": {
        title: "欢迎使用 Hermes File Manager",
        message: "您已成功注册！首先创建一个团队或加入现有团队开始存储文件。",
        actions: [
            { label: "创建我的团队", action: "CREATE_TEAM", icon: "👥" },
            { label: "浏览现有团队", action: "LIST_TEAMS", icon: "🔍" }
        ],
        condition: (ctx) => ctx.teams.length === 0
    },

    "TEAM_JOINED": {
        title: "您已加入团队",
        message: "探索团队共享空间，上传您的第一个文件",
        actions: [
            { label: "上传文件", action: "UPLOAD_FILE", icon: "📤" },
            { label: "查看团队成员", action: "VIEW_MEMBERS", icon: "👥" }
        ],
        condition: (ctx) => ctx.firstUpload === false
    },

    "FIRST_FILE_UPLOADED": {
        title: "文件上传成功！",
        message: "了解如何与团队成员协作编辑和分享文件",
        actions: [
            { label: "分享给成员", action: "SHARE_FILE", icon: "🔗" },
            { label: "查看版本历史", action: "VIEW_VERSIONS", icon: "📜" },
            { label: "创建工作流", action: "CREATE_WORKFLOW", icon: "⚙️" }
        ],
        condition: (ctx) => ctx.uploadCount === 1
    },

    // 阶段2: 协作
    "MEMBER_INVITED": {
        title: "新成员已邀请",
        message: "了解如何设置成员权限和管理团队文件",
        actions: [
            { label: "设置权限", action: "SET_PERMISSIONS", icon: "🔐" },
            { label: "创建团队工作流", action: "CREATE_TEAM_WORKFLOW", icon: "⚙️" }
        ],
        condition: (ctx) => ctx.memberCount > 1
    },

    "WORKFLOW_EXECUTED": {
        title: "工作流执行成功",
        message: "您已完成第一个自动化工作流！探索更多高级功能",
        actions: [
            { label: "查看执行记录", action: "VIEW_EXECUTION_LOG", icon: "📋" },
            { label: "创建笔记本", action: "CREATE_NOTEBOOK", icon: "📓" }
        ],
        condition: (ctx) => ctx.workflowExecuted === true
    },

    // 阶段3: 进阶
    "PRIVATE_SPACE_REQUESTED": {
        title: "私人空间申请已提交",
        message: "等待团队所有者审核。同时，您可以创建笔记本记录学习笔记",
        actions: [
            { label: "创建学习笔记", action: "CREATE_NOTEBOOK", icon: "📓" },
            { label: "查看申请状态", action: "VIEW_REQUEST_STATUS", icon: "📊" }
        ],
        condition: (ctx) => ctx.privateSpaceStatus === "pending"
    },

    "QUOTA_WARNING": {
        title: "存储空间即将用尽",
        message: "您的空间配额已使用超过80%，请及时清理或申请扩容",
        actions: [
            { label: "查看回收站", action: "OPEN_TRASH", icon: "🗑️" },
            { label: "申请扩容", action: "REQUEST_QUOTA", icon: "📈" },
            { label: "了解配额", action: "LEARN_QUOTA", icon: "💡" }
        ],
        condition: (ctx) => ctx.quotaUsage > 0.8
    },

    // 阶段4: 专家
    "CROSS_TEAM_COLLABORATION": {
        title: "跨团队协作已建立",
        message: "您现在可以跨团队共享文件和笔记，探索高级协作功能",
        actions: [
            { label: "创建共享笔记本", action: "CREATE_SHARED_NOTEBOOK", icon: "📓" },
            { label: "设置跨团队工作流", action: "CREATE_CROSS_TEAM_WORKFLOW", icon: "🔄" },
            { label: "查看协作分析", action: "VIEW_COLLAB_ANALYTICS", icon: "📊" }
        ],
        condition: (ctx) => ctx.crossTeamSpaces > 0
    }
};
```

---

## 空间功能集成 - 工作流 & 笔记本

### 工作流场景

| 场景 | 工作流名称 | 触发条件 | 新手引导 |
|------|-----------|---------|---------|
| 文件归档 | 自动归档流程 | 文件超过30天未修改 | "定期清理存储空间，保持高效协作" |
| 审批流程 | 文件审批流程 | 上传重要文件时 | "了解文件审批流程，确保合规" |
| 数据备份 | 自动备份流程 | 每周五下午 | "设置自动备份，防止数据丢失" |

### 工作流创建引导

```
引导节点1: 创建工作流
  → 点击「新建工作流」
  → 选择「文件归档流程」模板
  → 配置步骤: 触发条件 → 审核 → 归档

引导节点2: 执行工作流
  → 选择文件 → 点击「执行工作流」
  → 查看执行状态和历史记录

引导节点3: 团队工作流
  → 分享工作流给团队成员
  → 设置团队协作规则
```

### 笔记本场景

| 场景 | 笔记本用途 | 新手引导 |
|------|----------|---------|
| 学习笔记 | 关联到 Space，记录学习心得 | "将笔记本关联到项目空间，协作更高效" |
| 会议纪要 | 实时协同编辑，自动保存 | "创建会议纪要，自动同步到空间" |
| 需求文档 | 产品需求文档，版本管理 | "使用笔记本记录需求，自动追踪变更" |
| 团队知识库 | 汇总团队文档和笔记 | "创建团队知识库，统一管理资料" |

### 笔记本创建引导

```
引导节点1: 创建笔记本
  → 点击「+ 新建笔记本」
  → 输入名称和标签（项目/学习/会议）
  → 关联到当前 Space

引导节点2: 协作编辑
  → 邀请团队成员协编辑
  → 使用 Markdown 格式化
  → 自动保存历史版本

引导节点3: 知识沉淀
  → 将笔记本与文件关联
  → 设置提醒和到期时间
  → 定期回顾整理
```

---

## 引导触发机制

### 前端事件监听

```javascript
class GuidanceEngine {
    constructor() {
        this.listeners = new Map();
        this.setupDefaultListeners();
    }

    setupDefaultListeners() {
        // 注册事件监听
        this.on("USER_REGISTERED", this.handleUserRegistered.bind(this));
        this.on("FIRST_FILE_UPLOADED", this.handleFirstUpload.bind(this));
        this.on("QUOTA_WARNING", this.handleQuotaWarning.bind(this));
        // ... 更多事件
    }

    // 触发引导
    trigger(event, context) {
        const handler = this.listeners.get(event);
        if (handler) {
            const shouldShow = handler.condition(context);
            if (shouldShow) {
                this.showGuidance(handler);
            }
        }
    }

    showGuidance(config) {
        const modal = new GuidanceModal({
            title: config.title,
            message: config.message,
            actions: config.actions.map(a => ({
                label: a.label,
                icon: a.icon,
                handler: () => this.executeAction(a.action)
            }))
        });
        modal.show();
    }
}

// 使用示例
const guidance = new GuidanceEngine();

// 用户首次上传文件后触发
guidance.trigger("FIRST_FILE_UPLOADED", {
    uploadCount: 1,
    spaceId: "space-123"
});
```

---

## 引导提示消息库

| 事件 | 提示标题 | 提示内容 | 引导操作 |
|------|---------|---------|---------|
| USER_REGISTERED | "欢迎加入！" | "创建或加入团队开始存储和分享文件" | 创建团队 / 浏览团队 |
| TEAM_JOINED | "您已加入" | "探索团队空间，上传第一个文件" | 上传文件 / 查看成员 |
| FIRST_FILE_UPLOADED | "上传成功！" | "了解如何与团队协作编辑和分享" | 分享 / 版本历史 / 工作流 |
| MEMBER_INVITED | "邀请已发送" | "设置成员权限，管理团队协作" | 设置权限 / 创建工作流 |
| WORKFLOW_EXECUTED | "流程完成！" | "探索更多自动化办公能力" | 查看日志 / 创建笔记本 |
| QUOTA_WARNING | "空间不足" | "清理文件或申请扩容，避免影响工作" | 回收站 / 申请扩容 |
| PRIVATE_SPACE_PENDING | "申请待审核" | "等待团队所有者审核，可先创建笔记" | 创建笔记本 / 查看状态 |
| CROSS_TEAM_COLLAB | "跨团队协作" | "您现在可以跨团队共享资源" | 共享笔记本 / 设置工作流 |

---

## 新手引导UI组件

### 引导弹窗设计

```html
<!-- 引导弹窗组件 -->
<div class="guidance-modal" id="guidanceModal">
    <div class="guidance-header">
        <span class="guidance-icon">🎯</span>
        <h3 class="guidance-title">引导标题</h3>
        <button class="guidance-close" onclick="closeGuidance()">×</button>
    </div>
    <div class="guidance-body">
        <p class="guidance-message">引导说明内容</p>
        <div class="guidance-actions">
            <button class="guidance-action-btn primary">
                <span class="action-icon">📤</span>
                <span class="action-label">操作1</span>
            </button>
            <button class="guidance-action-btn secondary">
                <span class="action-icon">👥</span>
                <span class="action-label">操作2</span>
            </button>
        </div>
    </div>
    <div class="guidance-footer">
        <label class="guidance-dismiss">
            <input type="checkbox" onchange="dismissGuidance(event)">
            不再显示此类提示
        </label>
    </div>
</div>
```

### Coach Mark 设计

```html
<!-- 悬浮提示组件 -->
<div class="coach-mark" data-target="uploadBtn">
    <div class="coach-arrow"></div>
    <div class="coach-content">
        <p>点击此处上传文件</p>
        <button class="coach-next" onclick="nextStep()">下一步</button>
    </div>
</div>
```

---

## 最佳实践总结

### 领域最佳实践

**属于领域**：企业级文件管理 / 云存储协作平台

**最佳实践方法**：

1. **事件驱动而非强制引导**：用户操作时提供适时帮助，而非一次性灌输
2. **渐进式披露**：先展示核心功能，高级功能按需引导
3. **行动导向**：每个引导都指向具体可执行的操作
4. **上下文感知**：根据用户当前状态和历史行为调整引导内容
5. **容错与纠正**：允许用户犯错，提供纠正路径而非阻止操作

### 实施建议

1. **优先级排序**：先实现高价值引导（上传、协作、共享）
2. **数据驱动**：跟踪引导接受率和完成率，持续优化
3. **A/B测试**：测试不同引导策略的效果
4. **用户反馈**：收集用户对引导的反馈，不断迭代

---

## 相关文档

- [系统架构文档](./SYSTEM_ARCHITECTURE.md)
- [生命周期约束](./LIFECYCLE_CONSTRAINTS.md)
- [工作流服务](../services/workflow_service.py)
- [笔记本服务](../services/notebook_service.py)