# 资源申请审批流程 (Resource Approval Flow)

> **版本**: 1.1
> **更新日期**: 2026-05-05
> **项目**: Hermes File Manager
> **状态**: ✅ 已实现
>
> **更新说明 v1.1**: T4/T5/T6 任务已全部完成，审批数据模型、业务流程、API与前端集成均已实现

---

## 一、审批领域模型

### 1.1 核心实体

```
┌─────────────────────────────────────────────────────────────────┐
│                        申请单 (ApprovalRequest)                  │
├─────────────────────────────────────────────────────────────────┤
│  id: UUID                                                       │
│  type: ApprovalType (资源类型)                                  │
│  applicant_id: UUID (申请人)                                    │
│  target_id: UUID (目标资源ID)                                   │
│  status: RequestStatus (状态)                                   │
│  reason: Text (申请理由)                                        │
│  created_at: DateTime                                           │
│  updated_at: DateTime                                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      审批记录 (ApprovalRecord)                    │
├─────────────────────────────────────────────────────────────────┤
│  id: UUID                                                       │
│  request_id: UUID (关联申请单)                                  │
│  approver_id: UUID (审批人)                                     │
│  decision: Decision (approve/reject)                            │
│  comment: Text (审批意见)                                       │
│  decided_at: DateTime                                           │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 申请类型枚举

```python
class ApprovalType(str, Enum):
    """资源申请类型"""
    JOIN_TEAM = "join_team"              # 申请加入团队
    PRIVATE_SPACE = "private_space"     # 申请私人空间
    QUOTA_EXTEND = "quota_extend"       # 申请配额扩展
    STORAGE_POOL = "storage_pool"       # 申请存储池（仅管理员）
    TEAM_CREATE = "team_create"         # 申请创建团队（管理员审批）

class RequestStatus(str, Enum):
    """申请状态"""
    PENDING = "pending"      # 待审批
    APPROVED = "approved"    # 已批准
    REJECTED = "rejected"    # 已拒绝
    CANCELLED = "cancelled"  # 已取消
```

---

## 二、审批流程设计

### 2.1 流程图

```
用户申请资源
     │
     ↓
┌─────────────────┐
│  创建申请单      │
│  type, reason    │
└────────┬────────┘
         │
    ┌────┴────┬────────────┬─────────────┐
    ↓        ↓            ↓            ↓
  加入团队  私人空间    配额扩展     创建团队
    │        │            │            │
    │        │            │            │
    ↓        ↓            ↓            ↓
  管理员    管理员        管理员        管理员
  审批      审批         审批         审批
    │        │            │            │
    └────────┴────────────┴────────────┘
         │
         ↓
┌─────────────────┐
│  记录审批结果    │
│  分配/拒绝资源   │
└────────┬────────┘
         │
         ↓
    通知申请人
```

### 2.2 申请场景与审批规则

| 申请类型 | 申请人 | 审批人 | 审批条件 | 通过后操作 |
|---------|--------|--------|---------|----------|
| **JOIN_TEAM** | 普通用户 | 管理员 | 团队存在且未满员 | 添加用户到团队 |
| **PRIVATE_SPACE** | 普通用户 | 管理员 | 配额充足 | 创建私人空间 |
| **QUOTA_EXTEND** | 团队所有者 | 管理员 | 存储池有剩余配额 | 增加团队配额 |
| **STORAGE_POOL** | 管理员 | 系统 | - | 创建存储池 |
| **TEAM_CREATE** | 管理员 | 系统 | - | 创建团队 |

---

## 三、数据模型

### 3.1 申请单模型

```python
class ApprovalRequest(Base):
    """资源申请单"""
    __tablename__ = "hfm_approval_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String(32), nullable=False)  # ApprovalType
    applicant_id = Column(String(36), ForeignKey("hfm_users.id"), nullable=False)
    target_id = Column(String(36), nullable=True)  # 目标资源ID（如team_id）
    status = Column(String(16), default=RequestStatus.PENDING)
    reason = Column(Text, nullable=True)  # 申请理由

    # 申请参数（JSON格式存储）
    params = Column(JSON, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 审批信息
    approved_by = Column(String(36), ForeignKey("hfm_users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approval_comment = Column(Text, nullable=True)

    # 关系
    applicant = relationship("User", foreign_keys=[applicant_id])
    approver = relationship("User", foreign_keys=[approved_by])

    __table_args__ = (
        Index("ix_approval_request_applicant", "applicant_id"),
        Index("ix_approval_request_status", "status"),
        Index("ix_approval_request_type_status", "type", "status"),
    )
```

### 3.2 审批记录模型

```python
class ApprovalRecord(Base):
    """审批记录（审批链）"""
    __tablename__ = "hfm_approval_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(String(36), ForeignKey("hfm_approval_requests.id"), nullable=False)
    approver_id = Column(String(36), ForeignKey("hfm_users.id"), nullable=False)
    decision = Column(String(16), nullable=False)  # approve/reject
    comment = Column(Text, nullable=True)
    decided_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    request = relationship("ApprovalRequest")
    approver = relationship("User")

    __table_args__ = (
        Index("ix_approval_record_request", "request_id"),
    )
```

---

## 四、API 设计

### 4.1 申请接口

```python
# 创建申请单
POST /api/v1/approvals
{
    "type": "join_team",
    "target_id": "team-uuid",
    "reason": "需要访问团队文件"
}

# 获取我的申请列表
GET /api/v1/approvals/my?status=pending

# 取消申请
DELETE /api/v1/approvals/{request_id}
```

### 4.2 审批接口（管理员）

```python
# 获取待审批列表
GET /api/v1/approvals/pending?type=join_team

# 审批申请
POST /api/v1/approvals/{request_id}/decide
{
    "decision": "approve",  # approve / reject
    "comment": "同意加入"
}
```

### 4.3 查询接口

```python
# 获取某类型的申请统计
GET /api/v1/approvals/stats?type=private_space
{
    "pending": 5,
    "approved_today": 3,
    "rejected_today": 1
}
```

---

## 五、生命周期约束集成

### 5.1 申请前检查

```python
LIFECYCLE_CONSTRAINTS = {
    "request_join_team": (
        lambda ctx: not is_team_full(ctx["team_id"]),
        "该团队已达到人数上限，无法申请加入",
        "查看其他团队"
    ),
    "request_private_space": (
        lambda ctx: ctx["user"].quota_available > 0,
        "您的可用配额不足，无法申请私人空间",
        "申请配额扩展"
    ),
}
```

### 5.2 审批后触发

```python
def on_approval_approved(request: ApprovalRequest):
    """审批通过后的资源分配"""
    if request.type == ApprovalType.JOIN_TEAM:
        add_user_to_team(request.applicant_id, request.target_id)

    elif request.type == ApprovalType.PRIVATE_SPACE:
        create_private_space(
            user_id=request.applicant_id,
            parent_space_id=request.params.get("parent_space_id")
        )

    elif request.type == ApprovalType.QUOTA_EXTEND:
        extend_team_quota(
            team_id=request.target_id,
            additional_bytes=request.params.get("quota_bytes")
        )

def on_approval_rejected(request: ApprovalRequest):
    """审批拒绝后的通知"""
    send_notification(
        user_id=request.applicant_id,
        title="申请被拒绝",
        message=f"您的{request.type}申请已被拒绝，原因：{request.approval_comment}"
    )
```

---

## 六、前端集成

### 6.1 申请入口

| 场景 | 前端入口 | 显示条件 |
|------|---------|---------|
| 加入团队 | 团队详情页「申请加入」按钮 | 用户未加入该团队 |
| 私人空间 | 空间列表页「申请空间」按钮 | 用户无可用空间 |
| 配额扩展 | 团队设置页「申请扩展」按钮 | 仅团队所有者可见 |

### 6.2 审批界面

```
┌─────────────────────────────────────────────────────────────────┐
│  待审批申请 (3)                                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ [加入团队] 用户 limingq 申请加入 云计算团队              │     │
│  │ 申请时间: 2026-05-03 10:30                              │     │
│  │ 理由: 需要访问团队共享文档                               │     │
│  │                                                      │     │
│  │  [拒绝]  [批准]                                        │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ [私人空间] 用户 zhangsan 申请 500MB 私人空间             │     │
│  │ 申请时间: 2026-05-03 09:15                              │     │
│  │ 理由: 需要存放个人工作文档                               │     │
│  │                                                      │     │
│  │  [拒绝]  [批准]                                        │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 七、版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| 1.0 | 2026-05-03 | 初始版本：资源申请审批流程设计 |