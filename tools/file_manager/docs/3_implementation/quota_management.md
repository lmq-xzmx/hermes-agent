# 配额管理体系 (Quota Management)

> **版本**: 1.1
> **更新日期**: 2026-05-05
> **项目**: Hermes File Manager
> **状态**: ✅ 已实现
>
> **更新说明 v1.1**: T7/T8/T9 任务已全部完成，配额辅助函数、SELECT FOR UPDATE 防护、预警系统均已实现

---

## 一、领域概述

### 1.1 配额管理定位

配额管理是企业云存储平台的核心功能，用于：
- 控制资源分配防止超卖
- 保障用户公平使用存储资源
- 为商业化（购买/计费）预留接口

### 1.2 配额层级结构

```
┌─────────────────────────────────────────────────────────────────┐
│                     存储池配额 (Pool Quota)                      │
│  总容量: 10TB                                                    │
│  已分配: 8TB                                                     │
│  可用: 2TB                                                       │
│                         ↓                                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                 团队配额 (Team Quota)                       │  │
│  │  team_A: 3TB (已用 2.5TB)                                  │  │
│  │  team_B: 2TB (已用 1.8TB)                                  │  │
│  │  team_C: 3TB (已用 2TB)                                    │  │
│  │                           ↓                                │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │            空间配额 (Space Quota)                     │  │  │
│  │  │  team_A/开发空间: 1TB                                │  │  │
│  │  │  team_A/测试空间: 500GB                              │  │  │
│  │  │  team_A/张三私人空间: 200GB                          │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、配额类型定义

### 2.1 配额层级

| 层级 | 资源类型 | 管理角色 | 说明 |
|------|---------|---------|------|
| **L1 存储池** | StoragePool | 系统管理员 | 顶层资源池 |
| **L2 团队** | Team | 管理员/团队所有者 | 团队配额分配 |
| **L3 空间** | Space | 团队所有者/管理员 | 空间配额限制 |
| **L4 用户** | User | 管理员 | 用户个人配额 |

### 2.2 配额属性

```python
class QuotaConfig:
    """配额配置"""
    max_bytes: BigInteger      # 最大配额（字节）
    reserved_bytes: BigInteger # 已预留配额（用于进行中的上传）
    used_bytes: BigInteger    # 已使用配额
    warning_threshold: float   # 警告阈值（默认 80%）
    critical_threshold: float  # 危急阈值（默认 90%）

    @property
    def available_bytes(self) -> BigInteger:
        """可用配额 = 最大 - 已用 - 已预留"""
        return self.max_bytes - self.used_bytes - self.reserved_bytes

    @property
    def usage_ratio(self) -> float:
        """使用率 = 已用 / 最大配额"""
        return self.used_bytes / self.max_bytes if self.max_bytes > 0 else 0
```

---

## 三、配额计算规则

### 3.1 存储池配额计算

```python
def calculate_pool_available(pool_id: str) -> BigInteger:
    """
    存储池可用配额 = 总容量 - 已分配给团队的配额
    """
    pool = session.query(StoragePool).filter(StoragePool.id == pool_id).first()
    allocated = sum(team.quota_bytes for team in pool.teams)
    return pool.total_bytes - allocated
```

### 3.2 团队配额计算

```python
def calculate_team_available(team_id: str) -> BigInteger:
    """
    团队可用配额 = 团队配额上限 - 已分配给空间的配额
    """
    team = session.query(Team).filter(Team.id == team_id).first()
    allocated = sum(space.quota_bytes for space in team.spaces)
    return team.quota_bytes - allocated
```

### 3.3 空间配额计算

```python
def calculate_space_available(space_id: str) -> BigInteger:
    """
    空间可用配额 = 空间配额上限 - 已使用
    """
    space = session.query(Space).filter(Space.id == space_id).first()
    used = calculate_space_used(space_id)
    return space.quota_bytes - used
```

### 3.4 用户配额计算（个人空间）

```python
def calculate_user_available(user_id: str) -> BigInteger:
    """
    用户可用配额 = 个人空间配额上限 - 已使用
    """
    user = session.query(User).filter(User.id == user_id).first()
    personal_space = session.query(Space).filter(
        Space.owner_id == user_id,
        Space.type == "personal"
    ).first()

    if not personal_space:
        return 0

    used = calculate_space_used(personal_space.id)
    return personal_space.quota_bytes - used
```

---

## 四、超额防护机制

### 4.1 SELECT FOR UPDATE 悲观锁

```python
def check_quota_for_write_with_lock(space_id: str, additional_bytes: BigInteger, session: Session):
    """
    使用悲观锁检查配额，防止并发超卖
    """
    # 锁定 Space 记录
    space = session.query(Space).filter(
        Space.id == space_id
    ).with_for_update(nowait=False).first()

    # 计算预留配额（进行中的上传）
    reserved_bytes = session.query(func.sum(FileUpload.file_size)).filter(
        FileUpload.space_id == space_id,
        FileUpload.status.in_(["pending", "uploading"])
    ).scalar() or 0

    # 计算可用配额
    available = space.quota_bytes - space.used_bytes - reserved_bytes

    # 检查是否足够
    if additional_bytes > available:
        raise QuotaExceeded(
            f"配额不足: 需要 {additional_bytes} bytes，可用 {available} bytes"
        )

    return True
```

### 4.2 配额检查时机

| 操作 | 检查点 | 说明 |
|------|--------|------|
| 上传文件 | 文件上传前 | 检查空间可用配额 |
| 创建版本 | 版本创建前 | 检查配额是否足够 |
| 复制文件 | 复制操作前 | 检查目标空间配额 |
| 恢复删除 | 恢复操作前 | 检查配额是否足够 |

### 4.3 超额处理策略

```python
class QuotaExceededHandler:
    """配额超限处理"""

    def handle_upload(self, space_id: str, file_size: BigInteger, user_id: str):
        """处理上传超额情况"""

        # 1. 计算当前可用配额
        available = calculate_space_available(space_id)

        if file_size > available:
            # 2. 发送配额警告通知
            send_quota_warning(space_id, user_id, available, file_size)

            # 3. 尝试自动清理回收站释放空间
            freed = auto_cleanup_recycle_bin(space_id, file_size - available)
            if freed >= file_size - available:
                return True  # 清理成功，可以继续

            # 4. 抛出超额异常
            raise QuotaExceeded(
                message="空间配额不足，无法上传文件",
                space_id=space_id,
                required=file_size,
                available=available,
                suggestions=[
                    "清理回收站释放空间",
                    "申请配额扩展",
                    "删除不需要的文件"
                ]
            )

        return True
```

---

## 五、配额预警系统

### 5.1 预警级别

| 级别 | 阈值 | 颜色 | 动作 |
|------|------|------|------|
| **正常** | < 80% | 绿色 | 无 |
| **警告** | 80-90% | 黄色 | 发送通知 |
| **危急** | > 90% | 红色 | 阻止上传 + 通知 |
| **已满** | = 100% | 灰色 | 禁止写入 |

### 5.2 预警通知

```python
def check_quota_and_notify(space_id: str):
    """检查配额并发送预警通知"""

    space = session.query(Space).filter(Space.id == space_id).first()
    ratio = space.used_bytes / space.quota_bytes if space.quota_bytes > 0 else 0

    if ratio >= 0.9:
        send_critical_alert(
            to=space.owner,
            title=f"空间「{space.name}」配额已用尽 90%",
            message=f"已使用 {space.used_bytes} / {space.quota_bytes} bytes",
            actions=["申请扩展配额", "清理回收站"]
        )
    elif ratio >= 0.8:
        send_warning(
            to=space.owner,
            title=f"空间「{space.name}」配额即将用尽",
            message=f"已使用 {int(ratio*100)}%，请注意清理"
        )
```

---

## 六、商业化配额预留

### 6.1 资源计划定义

```python
class ResourcePlan(Base):
    """资源计划（商业化）"""
    __tablename__ = "hfm_resource_plans"

    id = Column(String(36), primary_key=True)
    name = Column(String(64), nullable=False)  # 免费版/专业版/企业版
    storage_bytes = Column(BigInteger, nullable=False)  # 存储配额
    team_count = Column(Integer, nullable=False)  # 最大团队数
    member_count = Column(Integer, nullable=False)  # 最大成员数
    price_monthly = Column(Numeric(10, 2), nullable=False)  # 月费
    price_yearly = Column(Numeric(10, 2), nullable=False)  # 年费

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    subscriptions = relationship("Subscription", back_populates="plan")
```

### 6.2 订阅模型

```python
class Subscription(Base):
    """用户订阅"""
    __tablename__ = "hfm_subscriptions"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("hfm_users.id"), nullable=False)
    plan_id = Column(String(36), ForeignKey("hfm_resource_plans.id"), nullable=False)

    status = Column(String(16), default="active")  # active, cancelled, expired
    started_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    # 计费信息
    billing_cycle = Column(String(16), default="monthly")  # monthly, yearly
    auto_renew = Column(Boolean, default=True)

    # 关系
    user = relationship("User", back_populates="subscription")
    plan = relationship("ResourcePlan", back_populates="subscriptions")
```

---

## 七、配额管理API

### 7.1 查询接口

```python
# 获取我的配额信息
GET /api/v1/my/quota
{
    "personal_space": {
        "quota_bytes": 5368709120,
        "used_bytes": 3221225472,
        "available_bytes": 2147483648,
        "usage_ratio": 0.6
    },
    "teams": [
        {
            "team_id": "xxx",
            "team_name": "云计算团队",
            "quota_bytes": 10737418240,
            "used_bytes": 8589934592,
            "available_bytes": 2147483648,
            "usage_ratio": 0.8
        }
    ]
}

# 获取存储池配额（管理员）
GET /api/v1/admin/storage_pools/{pool_id}/quota
{
    "total_bytes": 10995116277760,
    "allocated_bytes": 8796093022208,
    "available_bytes": 2199023255552,
    "team_allocations": [...]
}
```

### 7.2 管理接口（管理员）

```python
# 分配团队配额
POST /api/v1/admin/teams/{team_id}/quota
{
    "quota_bytes": 5368709120  # 5GB
}

# 调整空间配额
PATCH /api/v1/admin/spaces/{space_id}/quota
{
    "quota_bytes": 1073741824  # 1GB
}
```

---

## 八、实施检查清单

```
配额管理系统实施检查:
├── [ ] L1: 存储池配额模型
│   ├── [ ] StoragePool 模型添加 quota_bytes 字段
│   ├── [ ] 计算存储池可用配额
│   └── [ ] 超额时阻止团队创建
├── [ ] L2: 团队配额模型
│   ├── [ ] Team 模型添加 quota_bytes 字段
│   ├── [ ] 计算团队可用配额
│   └── [ ] 超额时阻止空间创建
├── [ ] L3: 空间配额模型
│   ├── [ ] Space 模型添加 quota_bytes 字段
│   ├── [ ] 计算空间可用配额
│   └── [ ] 超额时阻止文件上传
├── [ ] L4: 用户配额模型
│   ├── [ ] User 模型添加 personal_quota_bytes 字段
│   └── [ ] 个人空间配额限制
├── [ ] 超额防护
│   ├── [ ] SELECT FOR UPDATE 悲观锁
│   ├── [ ] 预留配额计算 (FileUpload)
│   └── [ ] 并发场景测试
├── [ ] 预警系统
│   ├── [ ] 配额检查定时任务
│   ├── [ ] 80%/90% 阈值预警
│   └── [ ] 通知发送
└── [ ] 商业化预留
    ├── [ ] ResourcePlan 模型
    ├── [ ] Subscription 模型
    └── [ ] 订阅检查逻辑
```

---

## 九、版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| 1.0 | 2026-05-03 | 初始版本：配额管理体系设计 |