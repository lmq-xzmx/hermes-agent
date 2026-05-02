# Hermes File Manager 架构文档索引

## 文档目录

```
docs/architecture/
├── README.md                    # 本索引文件
├── SYSTEM_ARCHITECTURE.md       # 系统架构总览
├── ADMIN_DASHBOARD.md          # Admin 信息可视化界面建议
├── LIFECYCLE_CONSTRAINTS.md     # 生命周期操作约束
└── NEW_USER_GUIDE.md            # 普通用户新手指导
```

---

## 文档概览

### 1. 系统架构总览 (SYSTEM_ARCHITECTURE.md)

**核心内容**：
- 系统架构概览图
- 新系统初始化步骤
- 新用户注册流程
- 新团队创建流程
- 空间与团队/用户关系
- 存储池分配机制
- 私人空间与团队空间关系
- 管理员与普通用户关系
- 生命周期总览图

**所属领域**：企业级文件管理 / 云存储协作平台

---

### 2. Admin 信息可视化界面建议 (ADMIN_DASHBOARD.md)

**核心内容**：
- 领域分类与最佳实践方法论
- Admin 控制台界面布局建议
- 核心可视化组件设计
- 操作拦截规则
- 新手引导事件驱动流程

**所属领域**：
- 多租户存储资源管理
- 基于角色的访问控制 (RBAC)
- 团队协作与空间隔离

---

### 3. 生命周期操作约束 (LIFECYCLE_CONSTRAINTS.md)

**核心内容**：
- 约束规则设计
- 用户语言提示设计
- 后端约束实现
- 前端错误处理
- 操作拦截流程图
- 约束规则表

**所属领域**：
- 操作约束与数据一致性保护
- 生命周期合规性管理

---

### 4. 普通用户新手指导 (NEW_USER_GUIDE.md)

**核心内容**：
- 用户旅程引导地图
- 事件驱动引导实现
- 工作流与笔记本功能集成
- 引导触发机制
- 引导提示消息库

**所属领域**：
- 基于事件的引导系统
- 工作流与知识协作

---

## 快速导航

### 按角色

| 角色 | 推荐文档 |
|------|---------|
| 系统管理员 | ADMIN_DASHBOARD.md, LIFECYCLE_CONSTRAINTS.md |
| 团队所有者 | SYSTEM_ARCHITECTURE.md, LIFECYCLE_CONSTRAINTS.md |
| 普通用户 | NEW_USER_GUIDE.md, SYSTEM_ARCHITECTURE.md |

### 按任务

| 任务 | 推荐文档 |
|------|---------|
| 理解系统架构 | SYSTEM_ARCHITECTURE.md |
| 设计管理界面 | ADMIN_DASHBOARD.md |
| 实现操作约束 | LIFECYCLE_CONSTRAINTS.md |
| 设计用户引导 | NEW_USER_GUIDE.md |

---

## 文档版本

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| 1.0 | 2026-05-02 | 初始版本 |

---

## 相关链接

- [系统规格说明](../SPEC.md)
- [API 接口文档](../api/)
- [数据模型](../engine/models.py)
- [工作流服务](../services/workflow_service.py)
- [笔记本服务](../services/notebook_service.py)