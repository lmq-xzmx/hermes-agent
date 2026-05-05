# 生命周期错误码契约文档

> **版本**: 1.1
> **更新日期**: 2026-05-05
> **目的**: 统一前后端错误码，确保 API 错误响应一致性
> **更新说明 v1.1**: 修正错误码格式与实际 lifecycle_engine.py 一致，更新前端引用路径

---

## 一、错误码规范

### 1.1 错误码格式

```
{Category}_{SpecificCode}

示例:
- STORAGE_POOL_IN_USE
- POOL_MIGRATING
- POOL_HAS_ACTIVE_OPS
```

### 1.2 错误码分类

| 前缀 | 类别 | 说明 |
|------|------|------|
| `AUTH_` | 认证相关 | 登录、Token、权限 |
| `LIFECYCLE_` | 生命周期约束 | 配额、成员、状态（已废弃，统一使用简化格式） |
| `STORAGE_` / `POOL_` | 存储池相关 | 存储池操作 |
| `SPACE_` | 空间相关 | 空间成员、状态 |
| `TEAM_` | 团队相关 | 团队成员、邀请 |
| `MEMBERSHIP_` | 成员资格 | 加入、审批 |
| `QUOTA_` | 配额相关 | 配额检查、更新 |
| `CREDENTIAL_` | 凭证相关 | 邀请码 |
| `SYSTEM_` | 系统错误 | 数据库、网络、外部服务 |

---

## 二、生命周期错误码

> **注意**: 错误码格式已简化，不再使用 `LIFECYCLE_` 前缀。以下错误码与 lifecycle_engine.py 中实际定义一致。

### 2.1 存储池相关

| Error Code | HTTP Status | 后端定义位置 | 说明 |
|------------|-------------|-------------|------|
| `STORAGE_POOL_IN_USE` | 409 | lifecycle_exception.py:16 | 存储池仍有团队使用 |
| `POOL_TEAMS_MIGRATING` | 409 | lifecycle_exception.py:18 | 存储池正在迁移中 |
| `POOL_HAS_ACTIVE_OPS` | - | (via lifecycle_engine) | 存储池有团队正在操作 |
| `NO_AVAILABLE_POOL` | 503 | lifecycle_exception.py:19 | 无可用存储池 |
| `POOL_CAPACITY_INSUFFICIENT` | - | (via lifecycle_engine) | 池容量不足 |

### 2.2 空间相关

| Error Code | HTTP Status | 后端定义位置 | 说明 |
|------------|-------------|-------------|------|
| `SPACE_HAS_MEMBERS` | 409 | lifecycle_engine.py:256 | 空间仍有成员 |
| `SPACE_HAS_PENDING_SHARES` | 409 | lifecycle_engine.py:237 | 有待处理分享 |
| `SPACE_TRANSFER_PENDING` | 409 | lifecycle_engine.py:245 | 空间转让中 |
| `NOT_SPACE_OWNER` | 403 | lifecycle_engine.py:285 | 非空间所有者 |
| `NOT_SPACE_MEMBER` | 403 | lifecycle_engine.py:397 | 非空间成员 |

### 2.3 团队相关

| Error Code | HTTP Status | 后端定义位置 | 说明 |
|------------|-------------|-------------|------|
| `NOT_TEAM_OWNER` | 403 | lifecycle_engine.py:427 | 非团队所有者 |
| `TEAM_MIGRATING` | 409 | lifecycle_engine.py:433 | 团队正在迁移中 |
| `TEAM_HAS_PENDING_INVITATIONS` | 409 | lifecycle_engine.py:442 | 有待处理邀请 |
| `NOT_TEAM_MEMBER` | 403 | lifecycle_engine.py:360 | 非团队成员 |
| `MEMBERSHIP_PENDING` | 403 | lifecycle_engine.py:367 | 成员资格待审批 |
| `TEAM_INACTIVE` | 403 | lifecycle_engine.py:513 | 团队已解散 |
| `MEMBER_LIMIT_REACHED` | 403 | lifecycle_engine.py:521 | 成员数已达上限 |
| `ALREADY_TEAM_MEMBER` | 409 | lifecycle_engine.py:507 | 已是团队成员 |

### 2.4 配额相关

| Error Code | HTTP Status | 后端定义位置 | 说明 |
|------------|-------------|-------------|------|
| `SPACE_QUOTA_EXCEEDED` | 403 | lifecycle_exception.py:27 | 空间配额已用尽 |
| `SPACE_QUOTA_RESERVED` | 409 | lifecycle_exception.py:28 | 空间配额被并发上传临时占用 |
| `TEAM_QUOTA_EXCEEDED` | 403 | lifecycle_exception.py:34 | 团队配额已用尽 |
| `MEMBER_LIMIT_EXCEEDED` | 403 | lifecycle_exception.py:33 | 成员数已达上限 |
| `QUOTA_LESS_THAN_USAGE` | 400 | (via lifecycle_engine) | 新配额小于已用 |

### 2.5 凭证相关

| Error Code | HTTP Status | 后端定义位置 | 说明 |
|------------|-------------|-------------|------|
| `INVALID_CREDENTIAL` | 403 | lifecycle_engine.py:498 | 邀请码无效 |
| `CREDENTIAL_EXPIRED` | 403 | lifecycle_engine.py:492 | 邀请码已过期 |
| `INVITATION_PENDING` | 409 | lifecycle_engine.py:352 | 有待处理邀请 |

---

## 三、API 错误响应格式

### 3.1 统一错误响应格式

```json
{
  "error": {
    "code": "QUOTA_EXCEEDED",
    "message": "存储配额已用尽，无法上传新文件",
    "details": {
      "space_name": "项目A",
      "used_bytes": 1024000000,
      "max_bytes": 1024000000,
      "required_bytes": 5242880
    },
    "guidance": {
      "action": "view_trash",
      "url": "/trash"
    }
  }
}
```

### 3.2 错误响应字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `error.code` | string | ✅ | 错误码，如 `QUOTA_EXCEEDED`, `NOT_SPACE_MEMBER` |
| `error.message` | string | ✅ | 用户友好的错误消息 |
| `error.details` | object | ❌ | 错误相关的额外数据 |
| `error.guidance` | object | ❌ | 引导用户操作 |
| `error.guidance.action` | string | ❌ | guidance action 名称，如 `view_trash`, `contact_admin` |
| `error.guidance.url` | string | ❌ | 跳转路径，如 `/trash`, `/admin` |

---

## 四、前端错误码映射

### 4.1 前后端 Error Code 对照表

| 后端 Error Code | 前端 Check 字段 | 前端 Error Title | 状态 |
|----------------|-----------------|-----------------|------|
| `STORAGE_POOL_IN_USE` | `teamCount > 0` | 无法删除存储池 | ✅ 已同步 |
| `POOL_MIGRATING` | `poolMigrating` | 存储池迁移中 | ✅ 已同步 |
| `POOL_HAS_ACTIVE_OPS` | `teamsWithActiveOps > 0` | 有团队正在操作 | ✅ 已同步 |
| `NO_AVAILABLE_POOL` | `!hasAvailablePool` | 无法创建团队 | ✅ 已同步 |
| `POOL_CAPACITY_INSUFFICIENT` | `poolCapacityInsufficient` | 存储池容量不足 | ✅ 已同步 |
| `SPACE_HAS_MEMBERS` | `memberCount > 0` | 无法删除空间 | ✅ 已同步 |
| `SPACE_HAS_PENDING_SHARES` | `pendingShareRequests > 0` | 有待处理分享 | ✅ 已同步 |
| `SPACE_TRANSFER_PENDING` | `transferPending` | 空间转让中 | ✅ 已同步 |
| `NOT_SPACE_OWNER` | `!isOwner` | 只有空间所有者... | ✅ 已同步 |
| `NOT_SPACE_MEMBER` | `!isMember` | 无法上传文件 | ✅ 已同步 |
| `NOT_TEAM_OWNER` | `!isOwner` | 只有团队所有者... | ✅ 已同步 |
| `NOT_TEAM_MEMBER` | `!isTeamMember` | 只有团队成员... | ✅ 已同步 |
| `MEMBERSHIP_PENDING` | `memberStatus === 'pending'` | 成员资格待审批 | ✅ 已同步 |
| `TEAM_INACTIVE` | `!teamActive` | 团队已解散 | ✅ 已同步 |
| `MEMBER_LIMIT_REACHED` | `memberCount >= memberLimit` | 成员已满 | ✅ 已同步 |
| `ALREADY_TEAM_MEMBER` | `alreadyMember` | 已是成员 | ✅ 已同步 |
| `QUOTA_EXCEEDED` | `!hasQuota` / `!sufficientQuota` | 配额不足 | ✅ 已同步 |
| `QUOTA_LESS_THAN_USAGE` | `newQuota < currentUsage` | 配额不能小于已用 | ✅ 已同步 |
| `INVALID_CREDENTIAL` | `!credentialValid && !credentialExpired` | 邀请码无效 | ✅ 已同步 |
| `CREDENTIAL_EXPIRED` | `credentialExpired` | 邀请码已过期 | ✅ 已同步 |

---

## 五、契约遵守检查

### 5.1 新增 Error Code 检查清单

```
添加新的 Error Code 时，必须：

1. [ ] 在本文档添加条目（包含 code、HTTP status、描述）
2. [ ] 在后端 lifecycle_engine.py 实现
3. [ ] 在前端 lifecycle-interceptor.js 添加 check
4. [ ] 在本文档更新"前后端对照表"
5. [ ] 编写单元测试覆盖此 error code
6. [ ] 在 OPTIMIZATION_AND_TEST_PLAN.md 添加 E2E 测试用例
```

### 5.2 契约违规检测

```python
# tests/test_error_code_contract.py

class TestErrorCodeContract:
    """错误码契约测试"""

    def test_all_backend_codes_have_frontent_mapping(self):
        """所有后端错误码必须在前端有映射"""
        backend_codes = get_backend_error_codes()  # 从 lifecycle_engine.py 提取
        frontend_codes = get_frontend_error_codes()  # 从 lifecycle-interceptor.js 提取

        missing = backend_codes - frontend_codes
        assert len(missing) == 0, f"缺失的前端映射: {missing}"

    def test_http_status_consistency(self):
        """HTTP 状态码必须一致"""
        # 验证后端返回的 HTTP status 与本文档一致
        pass
```

---

## 六、相关文档

- [TOP_DOWN_DEVELOPMENT.md](../1_architecture/TOP_DOWN_DEVELOPMENT.md) - 自顶向下开发方法论
- [OPTIMIZATION_AND_TEST_PLAN.md](../6_process/OPTIMIZATION_AND_TEST_PLAN.md) - 优化与测试计划
- [LIFECYCLE_CONSTRAINTS.md](../2_design/LIFECYCLE_CONSTRAINTS.md) - 生命周期约束设计
- [lifecycle_engine.py](../../services/lifecycle_engine.py) - 后端约束引擎
- [lifecycle-interceptor.js](../../web/js/lifecycle-interceptor.js) - 前端拦截器
