# ADR-006: 构建失败回滚

## 状态
✅ 已接受

## 日期
2026-05-05

## 背景
构建失败时需要自动恢复上一正常工作版本，避免系统不可用。

## 决策
实现完整的构建回滚机制：
- 构建前备份当前版本到 `/tmp/hermes-backup/`
- 构建失败时自动回滚
- 验证失败时也触发回滚

## 实现方式
```bash
# build.sh
rollback() {
    rsync -av --delete "$BACKUP_DIR/web/dist/" web/dist/
    rsync -av --delete "$BACKUP_DIR/bundle/" "$BUNDLE_DIR/"
}

# 验证失败也回滚
if ! verify_bundle; then
    rollback
    exit 1
fi
```

## 理由
1. **安全性**：构建失败不会导致系统不可用
2. **可靠性**：有回退方案敢于尝试新功能
3. **自动化**：无需人工干预

## 后果
- ✅ 构建可靠性提升
- ✅ 错误恢复自动化
- ⚠️ 磁盘空间占用增加

## 相关文档
- `GOALS.md` G7 - 构建失败回滚目标
- `scripts/build.sh` - 回滚实现
