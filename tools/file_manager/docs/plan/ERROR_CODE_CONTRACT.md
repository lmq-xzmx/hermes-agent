# 生命周期错误码契约文档

> **版本**: 1.0
> **更新日期**: 2026-05-02
> **目的**: 统一前后端错误码，确保 API 错误响应一致性

---

## 一、错误码规范

### 1.1 错误码格式

```
{Category}_{SpecificCode}

示例:
- LIFECYCLE_NOT_SPACE_MEMBER
- LIFECYCLE_QUOTA_EXCEEDED
- LIFECYCLE_STORAGE_POOL_IN_USE
```

### 1.2 错误码分类

| 前缀 | 类别 | 说明 |
|------|------|------|
| `AUTH_` | 认证相关 | 登录、Token、权限 |
| `LIFECYCLE_` | 生命周期约束 | 配额、成员、状态 |
| `RESOURCE_` | 资源操作 | 文件、空间、团队 |
| `SYSTEM_` | 系统错误 | 数据库、网络、外部服务 |

---

## 二、生命周期错误码 (LIFECYCLE_*)

### 2.1 存储池相关

| Error Code | HTTP Status | 后端定义位置 | 前端引用 | 说明 |
|------------|-------------|-------------|---------|------|
| `LIFECYCLE_STORAGE_POOL_IN_USE` | 409 | lifecycle_engine.py:195 | lifecycle-interceptor.js:77 | 存储池仍有团队使用 |
| `LIFECYCLE_POOL_MIGRATING` | 409 | lifecycle_engine.py:64 | lifecycle-interceptor.js:80 | 存储池正在迁移中 |
| `LIFECYCLE_POOL_HAS_ACTIVE_OPS` | 409 | lifecycle_engine.py:72 | lifecycle-interceptor.js:84 | 存储池有团队正在操作 |
| `LIFECYCLE_NO_AVAILABLE_POOL` | 503 | lifecycle_engine.py:244 | lifecycle-interceptor.js:46 | 无可用存储池 |
| `LIFECYCLE_POOL_CAPACITY_INSUFFICIENT` | 409 | lifecycle_engine.py:258 | lifecycle-interceptor.js:54 | 池容量不足 |

### 2.2 空间相关

| Error Code | HTTP Status | 后端定义位置 | 前端引用 | 说明 |
|------------|-------------|-------------|---------|------|
| `LIFECYCLE_SPACE_HAS_MEMBERS` | 409 | lifecycle_engine.py:215 | lifecycle-interceptor.js:102 | 空间仍有成员 |
| `LIFECYCLE_SPACE_HAS_PENDING_SHARES` | 409 | lifecycle_engine.py:220 | lifecycle-interceptor.js:104 | 有待处理分享 |
| `LIFECYCLE_SPACE_TRANSFER_PENDING` | 409 | lifecycle_engine.py:231 | lifecycle-interceptor.js:110 | 空间转让中 |
| `LIFECYCLE_NOT_SPACE_OWNER` | 403 | lifecycle_engine.py:226 | lifecycle-interceptor.js:136 | 非空间所有者 |
| `LIFECYCLE_NOT_SPACE_MEMBER` | 403 | lifecycle_engine.py:272 | lifecycle-interceptor.js:26 | 非空间成员 |
| `LIFECYCLE_SPACE_PENDING_REQUESTS` | 409 | lifecycle_engine.py:232 | N/A | 有待审核私人空间申请 |

### 2.3 团队相关

| Error Code | HTTP Status | 后端定义位置 | 前端引用 | 说明 |
|------------|-------------|-------------|---------|------|
| `LIFECYCLE_NOT_TEAM_OWNER` | 403 | lifecycle_engine.py:305 | lifecycle-interceptor.js:123 | 非团队所有者 |
| `LIFECYCLE_TEAM_MIGRATING` | 409 | lifecycle_engine.py:312 | lifecycle-interceptor.js:129 | 团队正在迁移中 |
| `LIFECYCLE_TEAM_HAS_PENDING_INVITATIONS` | 409 | lifecycle_engine.py:319 | lifecycle-interceptor.js:135 | 有待处理邀请 |
| `LIFECYCLE_NOT_TEAM_MEMBER` | 403 | lifecycle_engine.py:260 | lifecycle-interceptor.js:62 | 非团队成员 |
| `LIFECYCLE_MEMBERSHIP_PENDING` | 403 | lifecycle_engine.py:267 | lifecycle-interceptor.js:68 | 成员资格待审批 |
| `LIFECYCLE_TEAM_INACTIVE` | 403 | lifecycle_engine.py:345 | lifecycle-interceptor.js:199 | 团队已解散 |
| `LIFECYCLE_MEMBER_LIMIT_REACHED` | 403 | lifecycle_engine.py:350 | lifecycle-interceptor.js:203 | 成员数已达上限 |
| `LIFECYCLE_ALREADY_TEAM_MEMBER` | 409 | lifecycle_engine.py:340 | lifecycle-interceptor.js:193 | 已是团队成员 |

### 2.4 配额相关

| Error Code | HTTP Status | 后端定义位置 | 前端引用 | 说明 |
|------------|-------------|-------------|---------|------|
| `LIFECYCLE_QUOTA_EXCEEDED` | 403 | lifecycle_engine.py:279 | lifecycle-interceptor.js:30 | 配额已用尽 |
| `LIFECYCLE_QUOTA_LESS_THAN_USAGE` | 400 | lifecycle_engine.py:330 | lifecycle-interceptor.js:179 | 新配额小于已用 |
| `LIFECYCLE_QUOTA_RESERVED` | 409 | N/A | lifecycle-interceptor.js:28 | 并发上传配额预留 |

### 2.5 凭证相关

| Error Code | HTTP Status | 后端定义位置 | 前端引用 | 说明 |
|------------|-------------|-------------|---------|------|
| `LIFECYCLE_INVALID_CREDENTIAL` | 403 | lifecycle_engine.py:349 | lifecycle-interceptor.js:209 | 邀请码无效 |
| `LIFECYCLE_CREDENTIAL_EXPIRED` | 403 | lifecycle_engine.py:343 | lifecycle-interceptor.js:205 | 邀请码已过期 |
| `LIFECYCLE_INVITATION_PENDING` | 409 | lifecycle_engine.py:263 | N/A | 有待处理邀请 |

### 2.6 成员操作相关

| Error Code | HTTP Status | 后端定义位置 | 前端引用 | 说明 |
|------------|-------------|-------------|---------|------|
| `LIFECYCLE_MEMBER_RECENTLY_REMOVED` | 409 | lifecycle_engine.py:141 | lifecycle-interceptor.js:142 | 成员刚被移除 |

---

## 三、API 错误响应格式

### 3.1 统一错误响应格式

```json
{
  "error": {
    "code": "LIFECYCLE_QUOTA_EXCEEDED",
    "message": "存储配额已用尽，无法上传新文件",
    "details": {
      "space_name": "项目A",
      "used_bytes": 1024000000,
      "max_bytes": 1024000000,
      "required_bytes": 5242880
    },
    "guidance": {
      "label": "查看回收站",
      "icon": "🗑️",
      "action_type": "navigate",
      "path": "/trash"
    }
  }
}
```

### 3.2 错误响应字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `error.code` | string | ✅ | 错误码，与本文档一致 |
| `error.message` | string | ✅ | 用户友好的错误消息 |
| `error.details` | object | ❌ | 错误相关的额外数据 |
| `error.guidance` | object | ❌ | 引导用户操作 |
| `error.guidance.label` | string | ✅ | 引导按钮文本 |
| `error.guidance.icon` | string | ❌ | 引导图标 emoji |
| `error.guidance.action_type` | string | ✅ | navigate / callback / modal |
| `error.guidance.path` | string | ❌ | 跳转路径 (navigate) |
| `error.guidance.callback` | string | ❌ | 回调函数名 (callback) |

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

- [TOP_DOWN_DEVELOPMENT.md](./TOP_DOWN_DEVELOPMENT.md) - 自顶向下开发方法论
- [OPTIMIZATION_AND_TEST_PLAN.md](./OPTIMIZATION_AND_TEST_PLAN.md) - 优化与测试计划
- [LIFECYCLE_CONSTRAINTS.md](./LIFECYCLE_CONSTRAINTS.md) - 生命周期约束设计
- [lifecycle_engine.py](../../services/lifecycle_engine.py) - 后端约束引擎
- [lifecycle-interceptor.js](../../web/js/lifecycle-interceptor.js) - 前端拦截器
