# Hermes File Manager - 空间协作文件管理权限系统

## 1. Overview

**Name:** Hermes File Manager (HFM)
**Type:** Space collaboration file management system with fine-grained permission control and versioning
**Integration:** hermes-agent tool + REST API server

### Core Problem Solved

团队协作文件管理需要：
- **空间（Space）隔离**：不同项目/团队有独立的存储空间
- **层级管理**：根空间 → 子空间 → 团队/个人空间
- **配额控制**：每个空间有独立的硬盘配额
- **版本控制**：所有文件操作都有版本记录
- **权限管理**：基于角色的权限控制和审计追踪

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Clients                              │
│   ┌──────────┐  ┌──────────┐  ┌──────────────────────┐   │
│   │ Hermès  │  │  Web UI  │  │  Mobile / CLI        │   │
│   │ Agent   │  │          │  │                      │   │
│   └────┬─────┘  └────┬─────┘  └──────────┬───────────┘   │
└─────────┼─────────────┼───────────────────┼───────────────┘
          │             │                   │
          │             ▼                   │
          │    ┌────────────────────┐       │
          │    │   REST API        │       │
          │    │   /api/v1/*       │       │
          │    └─────────┬──────────┘       │
          │              │                   │
          └──────────────┼───────────────────┘
                         │
┌────────────────────────▼───────────────────────────────────┐
│                   Permission Layer                            │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│   │ JWT Auth     │  │ RBAC Engine  │  │ Space Rules  │    │
│   │ & Sessions   │  │              │  │ Engine       │    │
│   └──────────────┘  └──────────────┘  └──────────────┘    │
└────────────────────────┬───────────────────────────────────┘
                         │
┌────────────────────────▼───────────────────────────────────┐
│                File Operations Layer                         │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  │
│   │ Storage  │  │ Version  │  │ Audit    │  │  Share  │  │
│   │ Engine   │  │ Control  │  │ Logger   │  │  Links  │  │
│   └──────────┘  └──────────┘  └──────────┘  └─────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Data Model

### 3.1 User

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| username | String | Unique login name |
| password_hash | String | bcrypt hash |
| email | String | Optional |
| role_id | UUID | FK to Role |
| created_at | Timestamp | Creation time |
| is_active | Boolean | Account status |

### 3.2 Space（空间 - 原 Team）

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | String | Space name |
| parent_id | UUID | FK to parent Space (null for root) |
| storage_pool_id | UUID | FK to StoragePool |
| owner_id | UUID | FK to User (creator) |
| max_bytes | BigInteger | Max quota (0 = unlimited) |
| used_bytes | BigInteger | Current usage |
| space_type | String | `root` / `team` / `private` |
| status | String | `active` / `pending` / `archived` |
| created_at | Timestamp | |
| updated_at | Timestamp | |

**Space Types:**
- `root`: 顶层空间，由 Admin 创建，划分物理硬盘
- `team`: 团队空间，属于某个 Root，Team 成员共享
- `private`: 私有空间，团队成员申请获批后获得

### 3.3 SpaceMember（空间成员）

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| space_id | UUID | FK to Space |
| user_id | UUID | FK to User |
| role | String | `owner` / `member` / `viewer` |
| quota_bytes | BigInteger | Personal quota within space (0 = use space default) |
| joined_at | Timestamp | |
| status | String | `active` / `pending` / `rejected` |

### 3.4 StoragePool（存储池）

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | String | Pool name |
| base_path | String | Physical path on disk |
| protocol | String | `local` / `smb` / `nfs` / `s3` |
| total_bytes | BigInteger | Total capacity |
| free_bytes | BigInteger | Available space |
| is_active | Boolean | |

### 3.5 FileVersion（文件版本）

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| file_id | UUID | FK to file |
| version | Integer | Version number |
| path | String | File path at this version |
| size | BigInteger | File size |
| checksum | String | SHA256 hash |
| created_by | UUID | FK to User |
| created_at | Timestamp | |
| action | String | `create` / `update` / `delete` |

### 3.6 SpaceRequest（空间请求）

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| space_id | UUID | Parent space |
| requester_id | UUID | FK to User |
| requested_name | String | Requested sub-space name |
| requested_bytes | BigInteger | Requested quota |
| reason | String | Reason for request |
| status | String | `pending` / `approved` / `rejected` |
| reviewed_by | UUID | FK to User (admin/owner) |
| reviewed_at | Timestamp | |
| review_note | String | Approval/rejection note |
| created_at | Timestamp | |

### 3.7 SpaceCredential（空间凭证）

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| space_id | UUID | FK to Space |
| token | String | Unique invite token |
| max_uses | Integer | Max uses (null = unlimited) |
| used_count | Integer | Current use count |
| expires_at | Timestamp | Expiration time |
| created_by | UUID | FK to User |
| is_active | Boolean | |
| created_at | Timestamp | |

### 3.8 AuditLog

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | FK to User |
| action | String | Action type |
| space_id | UUID | FK to Space (if applicable) |
| path | String | File path involved |
| version_id | UUID | FK to FileVersion (if applicable) |
| result | String | `success` / `denied` / `error` |
| ip_address | String | Client IP |
| metadata | JSON | Extra details |
| created_at | Timestamp | |

### 3.9 Role

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | String | `admin` / `editor` / `viewer` |
| permissions | JSON | Permission flags |
| is_system | Boolean | System role |

**Built-in Roles:**
- `admin`: Full access, space management
- `editor`: Read/write within assigned spaces
- `viewer`: Read-only within assigned spaces

---

## 4. Space Architecture

### 4.1 Hierarchy

```
Root Space (Admin 创建)
├── Team Space A (团队共享)
│   ├── TeamMember 1
│   ├── TeamMember 2
│   └── Private Space 1 (成员私有, 申请获批)
├── Team Space B (团队共享)
│   └── ...
└── Storage Pool 1 (物理存储)
```

### 4.2 Storage Layout

```
{storage_pool_base_path}/
└── spaces/
    └── {space_id}/
        ├── members/
        │   └── {user_id}/
        │       └── ... (user's private files)
        ├── shared/
        │   └── ... (team shared files)
        └── .versions/
            └── {file_id}/
                ├── v1
                ├── v2
                └── ...
```

### 4.3 Space Creation Flow

```
1. Admin 创建 StoragePool（指定物理路径和总容量）
2. Admin 创建 Root Space（绑定到 StoragePool）
3. Admin 创建 Team Space（设置团队配额）
4. Admin 为 Team Space 生成 Invite Credential
5. Team Member 使用 Credential 加入 Team Space
6. Team Member 在 Space 内创建/管理文件
```

### 4.4 Private Sub-Space Request Flow

```
1. Team Member 提交 Private Space 申请
   POST /api/v1/spaces/{space_id}/request
   Body: {"name": "my-project", "quota_bytes": 1073741824, "reason": "..."}

2. Admin 收到通知，审批申请
   PUT /api/v1/space-requests/{request_id}
   Body: {"status": "approved", "note": "OK"}

3. 审批通过后，系统创建 Private Space
4. Team Member 成为 Private Space Owner
```

---

## 5. Version Control

### 5.1 Version Lifecycle

```
File Create  → v1 (initial)
File Update  → v2, v3, v4... (each update increments)
File Delete  → marks version as deleted, retains history
```

### 5.2 Version Query

```
GET /api/v1/files/{file_id}/versions
Response: {
  "versions": [
    {"id": "...", "version": 3, "created_at": "...", "created_by": "..."},
    {"id": "...", "version": 2, "created_at": "...", "created_by": "..."},
    {"id": "...", "version": 1, "created_at": "...", "created_by": "..."}
  ]
}
```

### 5.3 Version Restore

```
POST /api/v1/files/{file_id}/restore
Body: {"version": 2}
→ Creates new version v4 copying content from v2
```

---

## 6. Permission Model

### 6.1 Permission Flags

| Flag | Description |
|------|-------------|
| read | View file/directory |
| write | Create/edit files |
| delete | Remove files |
| manage | Space settings, members |
| admin | All permissions |

### 6.2 Permission Resolution

```
User requests operation on /spaces/{space_id}/path/to/file

1. Find user's SpaceMembership for space_id
2. Check if user's role grants required permission
3. If private space, only owner/member has access
4. If team space, check role within space
5. Log all access attempts
```

---

## 7. API Specification

### 7.1 Authentication

```
POST /api/v1/auth/login
Body: {"username": "...", "password": "..."}
Response: {"token": "...", "user": {...}}

POST /api/v1/auth/logout
Header: Authorization: Bearer <token>
```

### 7.2 Space Management

```
GET    /api/v1/spaces                    # List user's spaces
POST   /api/v1/spaces                    # Create space (admin)
GET    /api/v1/spaces/{id}               # Get space details
PUT    /api/v1/spaces/{id}               # Update space
DELETE /api/v1/spaces/{id}               # Delete space (admin)

GET    /api/v1/spaces/{id}/members       # List members
POST   /api/v1/spaces/{id}/members       # Add member (admin)
DELETE /api/v1/spaces/{id}/members/{uid} # Remove member

POST   /api/v1/spaces/{id}/invite        # Generate invite credential
POST   /api/v1/spaces/join               # Join via credential
```

### 7.3 Space Requests

```
GET    /api/v1/space-requests            # List pending requests (admin)
POST   /api/v1/spaces/{id}/request       # Request private space
PUT    /api/v1/space-requests/{id}        # Approve/reject request
```

### 7.4 File Operations

```
GET    /api/v1/files/list                # List directory
POST   /api/v1/files/mkdir               # Create directory
POST   /api/v1/files/write               # Create/update file
GET    /api/v1/files/read                 # Read file
DELETE /api/v1/files                      # Delete file
POST   /api/v1/files/move                # Move file
POST   /api/v1/files/copy                # Copy file

GET    /api/v1/files/{id}/versions       # List versions
POST   /api/v1/files/{id}/restore        # Restore version
```

### 7.5 Admin Operations

```
GET    /api/v1/admin/users
POST   /api/v1/admin/users
PUT    /api/v1/admin/users/{id}
DELETE /api/v1/admin/users/{id}

GET    /api/v1/admin/storage-pools
POST   /api/v1/admin/storage-pools
PUT    /api/v1/admin/storage-pools/{id}

GET    /api/v1/admin/audit
```

---

## 8. Hermes Agent Integration

### 8.1 Tool Operations

```
space_list           - List user's spaces
space_create         - Create space (admin)
space_members        - List space members
file_manager_list    - List directory
file_manager_read    - Read file
file_manager_write   - Write file
file_manager_mkdir   - Create directory
file_manager_delete  - Delete file
file_versions        - List file versions
file_restore         - Restore version
```

---

## 9. Security Features

### 9.1 JWT Tokens
- Access token: 24 hours (1440 minutes)
- Refresh token: 30 days

### 9.2 Audit Retention
- Logs retained for 90 days (configurable)
- Manual cleanup: `POST /api/v1/admin/cleanup?target=audit`
- Auto cleanup: Configure external cron to call the cleanup API

### 9.3 Trash / Soft Delete
- Deleted files move to `_trash/` directory (30-day retention)
- Auto purge: `POST /api/v1/admin/cleanup?target=trash`
- Combined cleanup: `POST /api/v1/admin/cleanup?target=all`

### 9.4 Path Traversal Prevention
```python
def safe_resolve(base: str, user_path: str) -> str:
    resolved = Path(base).resolve() / user_path.lstrip("/")
    if not str(resolved).startswith(base):
        raise PermissionError("Path traversal detected")
    return str(resolved)
```

### 9.5 In-App Notifications
- Quota warnings: 80%/90%/100% triggers notification to space owner
- Notification types: "quota_warning", "space_invite", "collaboration", "system"
- API endpoints:
  - `GET /api/v1/notifications` - List notifications
  - `GET /api/v1/notifications/unread-count` - Get unread count
  - `PUT /api/v1/notifications/{id}/read` - Mark as read
  - `PUT /api/v1/notifications/read-all` - Mark all as read
  - `DELETE /api/v1/notifications/{id}` - Delete notification

### 9.6 Audit Log Export
- Query audit logs: `GET /api/v1/admin/audit`
- Export formats: JSON (default), CSV
- Request body: `{ ..., "export_format": "csv" }`

---

## 10. File Structure

```
tools/file_manager/
├── SPEC.md
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── auth.py
│   ├── files.py
│   ├── spaces.py
│   ├── admin.py
│   └── dto.py
├── engine/
│   ├── __init__.py
│   ├── models.py
│   ├── storage.py
│   └── permission.py
├── services/
│   ├── __init__.py
│   ├── auth_service.py
│   ├── file_service.py
│   ├── space_service.py
│   ├── team_service.py      # Legacy, to be renamed
│   └── version_service.py
├── src-tauri/
│   ├── src/
│   │   ├── main.rs
│   │   ├── server.rs        # Rust API server
│   │   ├── db.rs
│   │   └── models.rs
│   └── Cargo.toml
└── tests/
```

---

## 11. Acceptance Criteria

- [x] mkdir function implemented in Rust Tauri server
- [x] Space hierarchy: Root → Team → Private (data models implemented)
- [x] Admin creates StoragePool and Root Space (SpaceService.create_pool, create_space)
- [x] Admin creates Team Spaces with quotas (SpaceService.create_space)
- [x] Team Members join via Credential (SpaceService.join_via_credential)
- [x] File operations logged with versions (FileService._create_version, list_versions)
- [x] Private Space requests and approval workflow (SpaceService.create_request, approve_request, reject_request)
- [x] Audit trail for all operations (existing EventBus/AuditLogger)
- [x] RBAC permission enforcement (existing PermissionChecker)
