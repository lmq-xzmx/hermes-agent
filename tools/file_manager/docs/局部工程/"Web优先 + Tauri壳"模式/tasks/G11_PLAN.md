# G11: Tauri 自动更新

> **版本**: v1.0
> **日期**: 2026-05-05
> **状态**: 📋 规划中
> **前置条件**: G10 (Tauri 按需打包) 达成后

---

## 1. 背景与目标

当前 Tauri 应用需要用户手动下载安装包更新。目标：实现自动更新功能，用户无感知升级。

**目标**:
- 检测到新版本时自动提示用户
- 支持后台下载、前台安装
- 回滚机制保障更新安全

---

## 2. 当前状态分析

### 2.1 现状

- 版本号：`tauri.conf.json` 中 `version: "1.0.0"`
- 无自动更新配置
- 用户需手动下载安装包

### 2.2 Tauri Updater 插件

Tauri 2.x 提供 `@tauri-apps/plugin-updater` 实现自动更新：

```toml
# Cargo.toml
tauri-plugin-updater = "2"
```

---

## 3. 自动更新架构

### 3.1 更新流程

```
┌─────────────────┐
│  启动应用        │
└────────┬────────┘
         ↓
┌─────────────────┐
│  检查更新 endpoint│
└────────┬────────┘
         ↓
    有新版本? ──否──→ 正常运行
         │
        是
         ↓
┌─────────────────┐
│  提示用户        │
└────────┬────────┘
         ↓
┌─────────────────┐
│  下载更新包      │
└────────┬────────┘
         ↓
┌─────────────────┐
│  安装并重启      │
└─────────────────┘
```

### 3.2 更新签名机制

为保障安全，更新包必须签名验证：

```
┌─────────────────────────────────────────┐
│  签名流程                                │
├─────────────────────────────────────────┤
│  1. 生成 RSA-4096 密钥对                 │
│  2. 私钥用于签署发布包                   │
│  3. 公钥嵌入应用                         │
│  4. 更新时验证签名                       │
└─────────────────────────────────────────┘
```

---

## 4. 规划方案

### 4.1 tauri.conf.json 配置

```json
// tauri.conf.json
{
  "plugins": {
    "updater": {
      "endpoints": [
        "https://releases.yourdomain.com/{{target}}/{{arch}}/{{current_version}}"
      ],
      "pubkey": "YOUR_ED25519_PUBLIC_KEY"
    }
  }
}
```

### 4.2 Cargo.toml 依赖

```toml
# Cargo.toml
[dependencies]
tauri-plugin-updater = "2"
```

### 4.3 前端调用示例

```javascript
// 引入 updater 插件
import { check } from '@tauri-apps/plugin-updater'

async function checkForUpdates() {
  const update = await check()
  if (update) {
    // 显示更新对话框
    await update.downloadAndInstall()
  }
}
```

### 4.4 更新服务器端点

建议的目录结构：

```
releases.yourdomain.com/
└── hermes-file-manager/
    └── macos/
        └── universal/
            ├── 1.0.0.json    # 更新清单
            ├── 1.0.0.app.tar.gz  # 签名包
            └── 1.1.0.json
            └── 1.1.0.app.tar.gz
```

### 4.5 更新清单格式 (manifest.json)

```json
{
  "version": "1.1.0",
  "date": "2026-05-10",
  "notes": "Bug fixes and performance improvements",
  "platforms": {
    "macos": {
      "signature": "base64_encoded_signature",
      "filename": "Hermes File Manager-1.1.0.app.tar.gz",
      "size": 52428800
    }
  }
}
```

---

## 5. 实施步骤

### Phase 1: 基础集成 (G11.1)

- [ ] 添加 `tauri-plugin-updater` 依赖
- [ ] 配置 updater plugin
- [ ] 生成签名密钥对
- [ ] 创建更新 endpoint (可先用 GitHub Releases)

### Phase 2: 前端集成 (G11.2)

- [ ] 引入 `@tauri-apps/plugin-updater`
- [ ] 实现更新检查 UI
- [ ] 处理下载进度显示
- [ ] 实现安装后重启逻辑

### Phase 3: 发布流程 (G11.3)

- [ ] 创建签名脚本
- [ ] 配置 CI/CD 自动发布
- [ ] 测试完整更新流程

### Phase 4: 回滚机制 (G11.4)

- [ ] 实现更新前备份
- [ ] 失败时自动回滚
- [ ] 用户可选择是否回滚

---

## 6. 安全考虑

| 风险 | 缓解措施 |
|------|---------|
| 中间人攻击 | 更新包必须签名验证 |
| 恶意更新包 | 仅接受与公钥匹配的签名 |
| 更新失败 | 实现备份和回滚机制 |
| 版本回退 | 支持降级（可选） |

---

## 7. 相关文档

- [GOALS.md](../GOALS.md) - 目标体系
- [G10_PLAN.md](./G10_PLAN.md) - Tauri 按需打包规划
- [Tauri Updater Plugin](https://tauri.app/plugin/updater/)

---

## 8. 变更记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-05-05 | 初始规划方案 |