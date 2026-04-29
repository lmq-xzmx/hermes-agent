# Hermes File Manager - 团队协作文件管理权限系统

## 1. Overview

**Name:** Hermes File Manager (HFM)
**Type:** Team collaboration file management system with fine-grained permission control
**Integration:** hermes-agent tool + REST API server

### Core Problem Solved

团队成员共享文件服务器时，需要：
- 不同成员对不同目录有不同权限（读/写/删/管理）
- 所有操作可审计追溯
- 支持账号密码登录
- 可作为 hermes-agent 工具使用，也可以独立 API 调用

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Clients                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ Hermès  │  │  Web UI  │  │  Mobile / CLI        │  │
│  │ Agent   │  │ (future) │  │                      │  │
│  └────┬─────┘  └────┬─────┘  └──────────┬───────────┘  │
└───────┼─────────────┼───────────────────┼──────────────┘
        │             │                   │
        │             ▼                   │
        │    ┌────────────────────┐        │
        │    │   REST API        │        │
        │    │   /api/v1/*       │        │
        │    └─────────┬──────────┘        │
        │              │                   │
        └──────────────┼───────────────────┘
                       │
┌───────────────────────▼───────────────────────────────┐
│               Permission Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ JWT Auth     │  │ RBAC Engine  │  │ Path Rules  │  │
│  │ & Sessions   │  │              │  │ Engine      │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└───────────────────────┬───────────────────────────────┘
                        │
┌───────────────────────▼───────────────────────────────┐
│               File Operations Layer                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ Storage  │  │ Audit    │  │ Admin    │  │ Share  │ │
│  │ Engine   │  │ Logger   │  │ API      │  │ Links  │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
└─────────────────────────────────────────────────────────┘
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
| updated_at | Timestamp | Last update |
| is_active | Boolean | Account status |
| last_login | Timestamp | Last login time |

### 3.2 Role

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | String | admin / editor / viewer / guest |
| description | String | Role description |
| is_system | Boolean | System role (cannot delete) |

**Built-in Roles:**
- `admin`: Full access to all paths, can manage users and roles
- `editor`: Read/write in allowed paths, cannot delete, cannot manage
- `viewer`: Read-only in allowed paths
- `guest`: Minimal read access, no write

### 3.3 PermissionRule

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| role_id | UUID | FK to Role |
| path_pattern | String | Glob pattern: `/shared/projects/**` |
| permissions | String | Comma-separated: `read,write,delete` |
| priority | Integer | Higher = overrides lower |
| created_by | UUID | FK to User |
| created_at | Timestamp | |

**Permission Flags:**
- `read` - View file/directory contents
- `write` - Create/edit files
- `delete` - Remove files/directories
- `manage` - Change permissions, share

### 3.4 AuditLog

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | FK to User |
| action | String | read / write / delete / login / etc |
| path | String | File path involved |
| result | String | success / denied / error |
| ip_address | String | Client IP |
| user_agent | String | Client info |
| metadata | JSON | Extra details |
| created_at | Timestamp | |

### 3.5 SharedLink

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| path | String | Shared file/directory path |
| token | String | Unique access token |
| password_hash | String | Optional password protection |
| expires_at | Timestamp | Expiration time |
| permissions | String | read or read_write |
| created_by | UUID | FK to User |
| access_count | Integer | Number of times accessed |
| created_at | Timestamp | |

---

## 4. Permission Rule Engine

### 4.1 Path Pattern Matching

```
/shared/projects/**         -> matches /shared/projects/file.txt, /shared/projects/sub/file.txt
/shared/public/*            -> matches /shared/public/file.txt, NOT /shared/public/sub/file.txt
/home/{username}/**         -> user-specific home directories
```

### 4.2 Rule Resolution Algorithm

```
1. Collect all rules matching user's role(s)
2. Filter rules where path_pattern matches target path
3. Sort by priority (descending)
4. Return first matching rule's permissions
5. If no match -> DENY
```

### 4.3 Permission Inheritance

- Directory permissions apply to all children unless overridden
- Explicit rule overrides inherited rule
- Higher priority wins at same path level

---

## 5. API Specification

### 5.1 Authentication

```
POST /api/v1/auth/login
Body: {"username": "alice", "password": "..."}
Response: {"token": "jwt...", "user": {...}, "expires_at": "..."}

POST /api/v1/auth/logout
Header: Authorization: Bearer <token>

POST /api/v1/auth/register  (admin only)
Body: {"username": "...", "password": "...", "role_id": "..."}
```

### 5.2 File Operations

```
GET    /api/v1/files/list        ?path=/shared/projects
POST   /api/v1/files/read        Body: {"path": "/shared/file.txt"}
POST   /api/v1/files/write       Body: {"path": "/shared/file.txt", "content": "..."}
POST   /api/v1/files/delete      Body: {"path": "/shared/file.txt"}
POST   /api/v1/files/move        Body: {"from": "...", "to": "..."}
POST   /api/v1/files/copy        Body: {"from": "...", "to": "..."}
POST   /api/v1/files/mkdir       Body: {"path": "/shared/newdir"}
GET    /api/v1/files/stat        ?path=/shared/file.txt
```

### 5.3 Admin Operations

```
GET    /api/v1/admin/users
POST   /api/v1/admin/users
PUT    /api/v1/admin/users/{id}
DELETE /api/v1/admin/users/{id}

GET    /api/v1/admin/roles
POST   /api/v1/admin/roles
PUT    /api/v1/admin/roles/{id}
DELETE /api/v1/admin/roles/{id}

GET    /api/v1/admin/rules
POST   /api/v1/admin/rules
PUT    /api/v1/admin/rules/{id}
DELETE /api/v1/admin/rules/{id}

GET    /api/v1/admin/audit
GET    /api/v1/admin/audit/export
```

### 5.4 Sharing

```
POST   /api/v1/share
Body: {"path": "/shared/file.txt", "password": "optional", "expires_in_days": 7}
Response: {"link": "https://hfm.example.com/s/abc123"}

GET    /api/v1/share/{token}
GET    /api/v1/share/{token}/download
```

---

## 6. Hermes Agent Integration

### 6.1 Tool Name

`file_manager` - 归属 toolset `file-manager`

### 6.2 Operations

```
file_manager_list     - List directory contents
file_manager_read     - Read file content
file_manager_write    - Write/create file
file_manager_delete   - Delete file or directory
file_manager_mkdir     - Create directory
file_manager_mv        - Move/rename file or directory
file_manager_cp       - Copy file or directory
file_manager_stat      - Get file/directory metadata
file_manager_share    - Create share link
```

### 6.3 Tool Schema

```json
{
  "name": "file_manager_list",
  "description": "List directory contents with permission checking",
  "parameters": {
    "type": "object",
    "properties": {
      "path": {"type": "string", "description": "Directory path to list"},
      "include_hidden": {"type": "boolean", "default": false}
    }
  }
}
```

### 6.4 Usage Flow

```
User (in Hermès) ──> file_manager_list ──> JWT from session ──> HFM API
                                         ──> Permission check ──> File system
                                         ──> Audit log ──> Return result
```

---

## 7. Security Features

### 7.1 JWT Tokens

- Access token expires in 24 hours
- Refresh token expires in 7 days
- Tokens stored in HTTP-only cookie (for web) or passed via header (for API)

### 7.2 Password Policy

- Minimum 8 characters
- bcrypt hashing with cost factor 12
- Optional: enforce complexity (numbers, special chars)

### 7.3 Rate Limiting

- Login: 5 attempts per minute per IP
- API: 100 requests per minute per user
- Share link access: 10 requests per minute per token

### 7.4 Path Traversal Prevention

```python
def safe_resolve(base: str, user_path: str) -> str:
    resolved = Path(base).resolve() / user_path.lstrip("/")
    if not str(resolved).startswith(base):
        raise PermissionError("Path traversal detected")
    return str(resolved)
```

### 7.5 Audit Retention

- Logs retained for 90 days by default
- Admin can export to CSV/JSON
- Automatic cleanup of old logs

---

## 8. Deployment

### 8.1 Standalone Mode

```bash
hfm-server --port 8080 \
  --storage /data/hfm \
  --jwt-secret your-secret-key
```

### 8.2 Docker Mode

```yaml
version: '3.8'
services:
  hfm:
    image: nousresearch/hermes-file-manager
    ports:
      - "8080:8080"
    volumes:
      - /shared/files:/data/hfm/files
      - /shared/config:/data/hfm/config
    environment:
      - HFM_JWT_SECRET=${JWT_SECRET}
      - HFM_PORT=8080
```

### 8.3 hermes-agent Integration

```yaml
# In config.yaml or .env
FILE_MANAGER_API_URL=http://localhost:8080
FILE_MANAGER_API_KEY=hermes-internal-api-key
```

---

## 9. File Structure

```
tools/file_manager/
├── SPEC.md
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── auth.py          # JWT login/logout/register
│   ├── files.py         # File CRUD operations
│   ├── admin.py         # User/role/rule management
│   ├── share.py         # Share link management
│   └── middleware.py    # Auth middleware, rate limiting
├── engine/
│   ├── __init__.py
│   ├── models.py        # SQLAlchemy models
│   ├── permission.py    # RBAC + path rules engine
│   ├── audit.py         # Audit logging
│   └── storage.py       # File system operations
├── tools/
│   ├── __init__.py
│   ├── registry.py      # Tool registration
│   ├── file_manager_tools.py  # Hermes tool implementations
│   └── schema.py        # Tool schemas
├── config.py            # Configuration
├── database.py          # DB connection & migrations
├── server.py            # FastAPI server entry point
└── tests/
    ├── __init__.py
    ├── test_permission_engine.py
    ├── test_auth.py
    ├── test_file_ops.py
    └── test_tools.py
```

---

## 10. Acceptance Criteria

- [ ] User can register and login with username/password
- [ ] JWT token returned and validated on each request
- [ ] Admin can create users and assign roles
- [ ] RBAC rules enforced on file operations
- [ ] Path glob patterns correctly match and resolve
- [ ] All file operations logged in audit trail
- [ ] Share links work with optional password protection
- [ ] hermes-agent can call file_manager tools with permission
- [ ] Rate limiting prevents brute force attacks
- [ ] Path traversal attempts are blocked
