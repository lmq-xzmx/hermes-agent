# HR Webhook 接口规范

> **创建日期**: 2026-05-24
> **用途**: HR 系统（飞书/企业微信/Workday）与 Hermes FM 对接规范
> **版本**: v1.0

---

## 一、概述

Hermes FM 提供标准 Webhook 接口，接收 HR 系统的入职/离职事件，自动完成员工账号配置。

### 1.1 支持的 HR 系统

| 系统 | 集成方式 | 状态 |
|------|---------|------|
| 飞书 | Webhook | 开发中 |
| 企业微信 | Webhook | 开发中 |
| Workday | REST API | 开发中 |

### 1.2 事件类型

| 事件 | 触发时机 | 操作 |
|------|---------|------|
| `employee.onboarding` | 新员工入职 | 自动创建账号、加入团队 Space |
| `employee.offboarding` | 员工离职 | 降级为 viewer、设置过期 |

---

## 二、安全机制

### 2.1 HMAC 签名验证

每个 Webhook 请求都携带 HMAC-SHA256 签名，用于验证请求来源。

**签名计算**：
```
signature = HMAC-SHA256(secret, timestamp + "." + payload)
```

**请求头**：
```
X-Hermes-Signature: sha256=<signature>
X-Hermes-Timestamp: <unix_timestamp>
```

**验证规则**：
1. 检查 `X-Hermes-Timestamp` 是否在 5 分钟内
2. 使用配置的 secret 计算签名
3. 与 `X-Hermes-Signature` 比对

### 2.2 IP 白名单

仅允许以下 IP 发送 Webhook：

```
# 在 config.yaml 中配置
webhook:
  allowed_ips:
    - "10.0.0.0/8"      # 内部网络
    - "HR_SYSTEM_IP"       # HR 系统 IP
```

---

## 三、入职事件

### 3.1 事件格式

```json
POST /api/admin/webhooks/onboarding
Content-Type: application/json
X-Hermes-Signature: sha256=abc123...
X-Hermes-Timestamp: 1716528000

{
  "event": "employee.onboarding",
  "event_id": "evt_20240624_001",
  "timestamp": "2026-06-01T09:00:00Z",
  "employee": {
    "external_id": "feishu_user_123",
    "name": "张三",
    "email": "zhangsan@company.com",
    "department": "技术部",
    "department_id": "dept_tech",
    "position": "后端开发",
    "hire_date": "2026-06-01",
    "manager": {
      "name": "李四",
      "email": "lisi@company.com"
    }
  },
  "settings": {
    "knowledge_share_policy": "full_share",
    "default_space": "hermes-tech",
    "role": "editor"
  }
}
```

### 3.2 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `event` | string | ✅ | 固定值 `employee.onboarding` |
| `event_id` | string | ✅ | 事件唯一 ID，用于幂等性 |
| `timestamp` | string | ✅ | ISO 8601 时间 |
| `employee.external_id` | string | ✅ | HR 系统中的员工 ID |
| `employee.name` | string | ✅ | 员工姓名 |
| `employee.email` | string | ✅ | 员工邮箱（登录凭证） |
| `employee.department` | string | ✅ | 部门名称 |
| `employee.department_id` | string | ✅ | 部门 ID |
| `employee.position` | string | ❌ | 职位 |
| `employee.hire_date` | string | ✅ | 入职日期 |
| `settings.knowledge_share_policy` | string | ✅ | 共享策略：`full_share` 或 `selective_share` |
| `settings.default_space` | string | ✅ | 默认加入的 Space |
| `settings.role` | string | ✅ | 角色：`editor` 或 `viewer` |

### 3.3 响应格式

**成功**：
```json
{
  "status": "success",
  "user_id": "hermes_user_456",
  "space_id": "hermes-tech",
  "message": "Employee onboarding completed"
}
```

**失败**：
```json
{
  "status": "error",
  "error_code": "DUPLICATE_USER",
  "message": "User with email already exists"
}
```

### 3.4 错误码

| 错误码 | 说明 | 处理方式 |
|--------|------|----------|
| `INVALID_SIGNATURE` | 签名验证失败 | 检查 secret 配置 |
| `TIMESTAMP_EXPIRED` | 时间戳过期 | 检查时钟同步 |
| `DUPLICATE_USER` | 用户已存在 | 跳过或更新现有用户 |
| `SPACE_NOT_FOUND` | Space 不存在 | 检查 `default_space` 配置 |
| `INVALID_DEPARTMENT` | 部门不存在 | 创建新部门或使用默认 |

---

## 四、离职事件

### 4.1 事件格式

```json
POST /api/admin/webhooks/offboarding
Content-Type: application/json
X-Hermes-Signature: sha256=def456...
X-Hermes-Timestamp: 1716528000

{
  "event": "employee.offboarding",
  "event_id": "evt_20261231_001",
  "timestamp": "2026-12-31T18:00:00Z",
  "employee": {
    "external_id": "feishu_user_123",
    "email": "zhangsan@company.com"
  },
  "settings": {
    "last_workday": "2026-12-31",
    "grace_period_days": 30,
    "export_personal": true
  }
}
```

### 4.2 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `event` | string | ✅ | 固定值 `employee.offboarding` |
| `event_id` | string | ✅ | 事件唯一 ID |
| `timestamp` | string | ✅ | ISO 8601 时间 |
| `employee.external_id` | string | ✅ | HR 系统中的员工 ID |
| `employee.email` | string | ✅ | 员工邮箱 |
| `settings.last_workday` | string | ✅ | 最后工作日 |
| `settings.grace_period_days` | int | ❌ | 宽限期天数，默认 30 |
| `settings.export_personal` | bool | ❌ | 是否允许导出个人笔记 |

### 4.3 响应格式

**成功**：
```json
{
  "status": "success",
  "user_id": "hermes_user_456",
  "actions": [
    {"action": "role_downgrade", "result": "viewer"},
    {"action": "set_expiry", "result": "2027-01-30"},
    {"action": "notify_employee", "result": "sent"}
  ],
  "message": "Employee offboarding completed"
}
```

---

## 五、配置示例

### 5.1 config.yaml 配置

```yaml
webhook:
  secret: "your-webhook-secret-key"
  allowed_ips:
    - "10.0.0.0/8"
    - "192.168.1.100"  # HR 系统 IP

hr_integration:
  enabled: true
  default_settings:
    knowledge_share_policy: "full_share"
    role: "editor"
    grace_period_days: 30
```

### 5.2 飞书 Webhook 配置

在飞书开放平台配置：

```
回调地址：https://your-domain.com/api/admin/webhooks/onboarding
加密密钥：<生成的加密密钥>
事件订阅：employee.onboarding, employee.offboarding
```

### 5.3 企业微信 Webhook 配置

在企业微信应用配置：

```
请求网址：https://your-domain.com/api/admin/webhooks/onboarding
Token：<随机生成的Token>
EncodingAESKey：<随机生成的AES Key>
```

---

## 六、测试接口

### 6.1 发送测试事件

```bash
curl -X POST https://your-domain.com/api/admin/webhooks/test \
  -H "Content-Type: application/json" \
  -H "X-Hermes-Signature: sha256=test" \
  -H "X-Hermes-Timestamp: $(date +%s)" \
  -d '{
    "event": "test",
    "message": "Hello Hermes"
  }'
```

### 6.2 验证签名

```python
import hmac
import hashlib
import time

def verify_signature(secret, timestamp, payload, signature):
    # 检查时间戳
    if int(time.time()) - int(timestamp) > 300:
        return False

    # 计算签名
    expected = hmac.new(
        secret.encode(),
        f"{timestamp}.{payload}".encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(f"sha256={expected}", signature)
```

---

## 七、相关文档

- [完全共享模式开发计划](./10_完全共享模式开发计划.md)
- [IT 预装验证 Checklist](./it-provisioning-checklist.md)
- [员工入职引导](./onboarding-checklist.md)