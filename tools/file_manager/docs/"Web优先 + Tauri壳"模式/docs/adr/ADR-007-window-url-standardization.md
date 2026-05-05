# ADR-007: 窗口 URL 标准化

> **状态**: 已接受
> **日期**: 2026-05-04
> **项目**: Hermes File Manager - Web优先 + Tauri壳模式

---

## 状态

已接受

---

## 问题

Tauri 2.x glob bug 导致无法使用标准路径 `app.html`

当前窗口 URL 配置：
```json
{
  "app": {
    "windows": [{
      "url": "_up_/web/dist/app.html"
    }]
  }
}
```

---

## 决策

接受 `_up_/web/dist/app.html` 作为当前标准路径

---

## 理由

1. **功能正常**：不影响用户使用体验
2. **Tauri bug 是临时的**：glob bug 会随 Tauri 版本更新修复
3. **迁移成本高**：手动复制方案增加构建复杂性
4. **低收益**：当前方案工作正常，改变反而引入风险

---

## 后果

- 路径依赖 Tauri glob 行为
- 等待 Tauri 修复后可回归标准路径 `app.html`
- `_up_` 前缀作为临时 workaround 记录在案

---

## 验证

```bash
# 确认窗口 URL 配置
grep -A5 "windows" src-tauri/tauri.conf.json
# 应显示: "url": "_up_/web/dist/app.html"
```

---

## 相关问题

- HIST-017: 非标准路径 `_up_/web/dist/`
- G8: 窗口 URL 标准化目标

---

## 参考

- [GOALS.md](../../GOALS.md) - 目标体系 G8
- [domain:Tauri&web.md](../../domain:Tauri&web.md) - 领域知识
