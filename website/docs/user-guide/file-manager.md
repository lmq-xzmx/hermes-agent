# File Manager 使用指南

Hermes File Manager (HFM) 是一个基于 Space 的团队协作文件管理系统，支持文件版本控制、权限管理、配额控制和软删除。

## 核心概念

### Space（空间）

Space 是文件管理的基本组织单元，采用层级结构：

| 类型 | 说明 |
|------|------|
| **Root Space** | 顶层空间，由管理员创建，绑定物理存储池 |
| **Team Space** | 团队共享空间，成员协作存放文件 |
| **Private Space** | 个人私有空间，需申请获批 |

### 存储池 (Storage Pool)

Storage Pool 是物理存储的抽象，绑定到服务器上的实际目录路径。每个 Space 归属于一个 Storage Pool。

### 权限模型

- **owner**: 空间所有者，拥有全部管理权限
- **member**: 空间成员，可读写文件
- **viewer**: 只读访问

---

## 快速开始

### 1. 登录

```
http://localhost:8080
```

使用用户名密码登录，系统会返回 Bearer Token。

### 2. 查看我的空间

登录后自动显示你所属的所有 Space，点击切换即可进入不同空间操作文件。

### 3. 文件操作

| 操作 | 说明 |
|------|------|
| **浏览** | 在文件列表中点击文件夹进入 |
| **新建文件夹** | 点击 "新建文件夹" 按钮 |
| **上传文件** | 点击 "上传" 按钮 |
| **下载** | 点击文件名旁的下载按钮 |
| **删除** | 点击删除按钮，文件移入回收站 |
| **移动/复制** | 使用移动或复制功能 |

---

## 回收站与软删除

### 工作原理

删除文件不会立即物理删除，而是：
1. 文件移动到 `_trash/` 目录
2. 数据库记录 DeletedFile（保留 30 天）
3. 30 天后可恢复或永久删除

### 恢复文件

1. 进入目标 Space
2. 点击左侧 "回收站" tab
3. 找到要恢复的文件，点击 "恢复"

### 永久删除

在回收站中点击 "永久删除"，文件将被物理删除且无法恢复。

---

## 配额管理

### 查看配额

进入 Space 后可在底部状态栏看到空间使用情况：
- 已用 / 总计
- 使用百分比

### 配额警告

当使用量达到 80%、90%、100% 时，系统会：
1. 发送站内通知给 Space owner
2. 在 UI 上显示警告色

### 配额不足处理

写入文件时如果配额不足，会收到明确错误提示。可联系 Space owner 申请扩容。

---

## 版本控制

### 查看历史

点击文件旁的 "历史" 按钮可查看该文件的所有版本。

### 恢复版本

在版本历史中，选择要恢复的版本，点击 "恢复"。系统会创建新版本，内容复制自选中版本。

---

## 定时清理

file_manager 提供 API 由外部系统调用进行定时清理：

```bash
# 清理回收站（删除 30 天前文件）
curl -X POST http://localhost:8080/api/v1/admin/cleanup?target=trash

# 清理审计日志（删除 90 天前记录）
curl -X POST http://localhost:8080/api/v1/admin/cleanup?target=audit

# 全量清理
curl -X POST http://localhost:8080/api/v1/admin/cleanup?target=all
```

### 使用 Hermes Agent 配置

你可以直接对 Hermes Agent 说：

```
/loop 24h 帮我清理 file_manager 回收站过期文件
/loop 24h 帮我清理 file_manager 过期审计日志
```

---

## Workflow（工作流）

Workflow 是保存的命令序列，可重复执行。

### 创建 Workflow

1. 进入某个 Space
2. 点击 "工作流" tab
3. 点击 "新建工作流"
4. 添加步骤（命令 + 说明）

### 执行 Workflow

点击工作流旁的 "▶ 执行" 按钮。

---

## 常见问题

**Q: 删除文件后多久会真正消失？**
A: 30 天后自动清理，也可手动清空回收站。

**Q: 如何分享文件给团队外的人？**
A: 当前版本建议通过共享链接（Shared Link）功能实现。

**Q: 存储池满了怎么办？**
A: 联系管理员创建新的 Storage Pool，或扩容现有 Pool。

---

## API 参考

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/spaces` | GET | 列出我的空间 |
| `/api/v1/files/list` | POST | 列出目录文件 |
| `/api/v1/files/write` | POST | 写入文件 |
| `/api/v1/files/mkdir` | POST | 创建目录 |
| `/api/v1/files/{id}` | DELETE | 删除文件 |
| `/api/v1/spaces/{id}/trash` | GET | 查看回收站 |
| `/api/v1/spaces/{id}/trash/{fid}/restore` | POST | 恢复文件 |
| `/api/v1/admin/cleanup` | POST | 执行清理任务 |