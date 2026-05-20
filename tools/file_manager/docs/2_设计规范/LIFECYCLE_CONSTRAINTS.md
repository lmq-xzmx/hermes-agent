# 生命周期操作约束

> **状态**: ✅ 已合并至 [MODULE_2_LIFECYCLE_CONSTRAINTS.md](./MODULE_2_LIFECYCLE_CONSTRAINTS.md)
>
> 本文档已废弃，所有内容已迁移至 MODULE_2_LIFECYCLE_CONSTRAINTS.md

---

## 内容迁移说明

以下内容已迁移至 [MODULE_2_LIFECYCLE_CONSTRAINTS.md](./MODULE_2_LIFECYCLE_CONSTRAINTS.md)：

| 原章节 | 目标位置 |
|--------|---------|
| 约束规则设计 | MODULE_2 §2.2 |
| 后端约束引擎 | MODULE_2 §2 |
| 约束装饰器 | MODULE_2 §2.3 |
| 服务层约束集成 | MODULE_2 §2.4 |
| 前端拦截器 | MODULE_2 §3 |
| 引导弹窗组件 | MODULE_2 §3.2 |
| 测试策略 | MODULE_2 §5 |
| 部署配置 | MODULE_2 §6 |

## 快速参考

### 约束规则表

| 操作 | 约束代码 | 前置条件 | 错误提示 |
|------|---------|---------|---------|
| upload_file | NOT_SPACE_MEMBER | 是 Space 成员 | "请先加入团队或空间才能上传文件" |
| upload_file | QUOTA_EXCEEDED | 配额足够 | "存储配额已用尽，无法上传新文件" |
| create_team | NO_AVAILABLE_POOL | 有可用存储池 | "系统暂无可用存储池" |
| delete_pool | STORAGE_POOL_IN_USE | 无团队使用 | "该存储池仍有团队使用" |
| invite_member | NOT_SPACE_OWNER | 是 Space Owner | "只有空间所有者可以邀请成员" |
| join_team | VALID_CREDENTIAL | 凭证有效 | "邀请码已过期或无效" |

> 完整约束规则表（含引导操作）请查看 [MODULE_2_LIFECYCLE_CONSTRAINTS.md](./MODULE_2_LIFECYCLE_CONSTRAINTS.md)

## 相关文档

- [MODULE_2_LIFECYCLE_CONSTRAINTS.md](./MODULE_2_LIFECYCLE_CONSTRAINTS.md) - 详细设计文档
- [ERROR_CODE_CONTRACT.md](../4_api/ERROR_CODE_CONTRACT.md) - 错误码契约
- [lifecycle_config.yaml](../4_api/lifecycle_config.yaml) - 配置溯源说明
