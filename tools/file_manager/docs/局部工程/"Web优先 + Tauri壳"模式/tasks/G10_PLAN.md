# G10: Tauri 按需打包

> **版本**: v1.0
> **日期**: 2026-05-05
> **状态**: 📋 规划中
> **前置条件**: G9 (Web 独立部署) 达成后

---

## 1. 背景与目标

当前 Tauri 打包配置为 `bundle.targets: ["app"]`，每次代码变更（无论前端还是Rust）都需要完整重新打包。

**目标**: 实现按需打包，仅在有原生需求变更时重新打包 Tauri，提升开发迭代效率。

---

## 2. 当前状态分析

### 2.1 现状

```json
// tauri.conf.json
{
  "bundle": {
    "active": true,
    "targets": ["app"],  // 仅 macOS app
    "icon": [...],
    "resources": {
      "../web/dist": ""  // 前端构建产物嵌入
    }
  }
}
```

### 2.2 问题

| 问题 | 影响 |
|------|------|
| 前端变更需要重新打包 Rust | 开发效率低 |
| 仅支持 macOS app | 无法发布 Windows/Linux 版本 |
| 无差异化打包策略 | 无法按需选择目标平台 |

---

## 3. 打包目标选项

Tauri 2.x 支持的打包目标：

| 目标 | 平台 | 说明 |
|------|------|------|
| `app` | macOS | macOS 应用包 (.app) |
| `dmg` | macOS | macOS 磁盘镜像 |
| `app-bundle` | macOS | 仅 .app bundle |
| `msi` | Windows | Windows Installer |
| `nsis` | Windows | NSIS 安装向导 |
| `deb` | Linux | Debian 包 |
| `rpm` | Linux | RedHat 包 |
| `appimage` | Linux | AppImage 便携包 |

---

## 4. 规划方案

### 4.1 打包策略分类

| 策略 | 触发条件 | 打包目标 |
|------|---------|----------|
| **前端变更** | Vue/JS/CSS 文件变更 | 无需重打包 Tauri |
| **Tauri 配置变更** | tauri.conf.json 修改 | 仅重建 bundle |
| **Rust 代码变更** | src-tauri/src/*.rs 修改 | 完整重建 |
| **资源变更** | icons/config 修改 | 仅重建 bundle |

### 4.2 推荐的 targets 配置

```json
// tauri.conf.json
{
  "bundle": {
    "active": true,
    "targets": ["dmg", "app"],  // macOS: dmg + app
    "icon": [...],
    "resources": {
      "../web/dist": ""
    },
    "category": "Productivity",
    "shortDescription": "File management with knowledge sync",
    "longDescription": "Hermes File Manager - Enterprise file management with knowledge synchronization"
  }
}
```

### 4.3 独立部署模式下的 resources 配置

当 G9 达成后，可切换为远程加载模式：

```json
// tauri.conf.json (G9 达成后)
{
  "app": {
    "windows": [{
      "url": "https://your-app.vercel.app"  // 远程加载
    }]
  },
  "bundle": {
    "resources": {}  // 无需嵌入本地资源
  }
}
```

---

## 5. 实施步骤

### Phase 1: 基础配置 (G10.1)

- [ ] 扩展 `bundle.targets` 支持 `dmg`
- [ ] 添加 dmg 专属配置（安装路径、授权协议）

### Phase 2: 构建脚本优化 (G10.2)

- [ ] 创建 `scripts/build-tauri-only.sh` - 仅重打包 Tauri
- [ ] 创建 `scripts/build-web-only.sh` - 仅重构建前端
- [ ] 创建 `scripts/build-full.sh` - 完整构建

### Phase 3: CI/CD 集成 (G10.3)

- [ ] GitHub Actions 配置多平台打包
- [ ] 发布流程自动化

---

## 6. 相关文档

- [GOALS.md](../GOALS.md) - 目标体系
- [G11_PLAN.md](./G11_PLAN.md) - Tauri 自动更新规划
- Tauri 2.x Bundle Configuration

---

## 7. 变更记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-05-05 | 初始规划方案 |