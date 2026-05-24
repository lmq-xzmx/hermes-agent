/**
 * Auto Sync Service - 保存即自动同步
 *
 * 监控文件变化并在保存时自动同步到团队 Space
 */

import { scanContent } from '../utils/sensitive_scan.js';
import { shouldSyncByTags, TagFilterMode } from '../utils/tag_filter.js';

export interface SyncResult {
  success: boolean;
  file_path: string;
  synced: boolean;
  skipped: boolean;
  reason?: string;
  error?: string;
}

export interface SyncOptions {
  mode: 'full' | 'selective';
  on_save: boolean;
  show_notifications: boolean;
}

/**
 * 自动同步单文件
 */
export async function autoSyncFile(
  filePath: string,
  content: string,
  options: SyncOptions
): Promise<SyncResult> {
  try {
    // 1. 敏感内容扫描
    const scanResult = scanContent(content, filePath);
    if (!scanResult.safe) {
      return {
        success: false,
        file_path: filePath,
        synced: false,
        skipped: true,
        reason: 'Sensitive content detected',
      };
    }

    // 2. 标签过滤
    const filterMode = options.mode === 'full' ? TagFilterMode.FULL : TagFilterMode.SELECTIVE;
    const tagCheck = shouldSyncByTags(content, filterMode);

    if (!tagCheck.shouldSync) {
      return {
        success: true,
        file_path: filePath,
        synced: false,
        skipped: true,
        reason: tagCheck.reason,
      };
    }

    // 3. 触发同步（调用 Hermes API）
    // TODO: 实现实际同步逻辑
    console.log(`[AutoSync] Syncing: ${filePath}`);

    return {
      success: true,
      file_path: filePath,
      synced: true,
      skipped: false,
    };
  } catch (error) {
    return {
      success: false,
      file_path: filePath,
      synced: false,
      skipped: false,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

/**
 * 显示同步状态提示（右下角）
 */
export function showSyncToast(result: SyncResult): void {
  if (!result.synced && result.skipped) {
    // 被跳过的文件不显示提示
    return;
  }

  const message = result.success
    ? `✅ 已同步到团队知识库`
    : `⚠️ 同步失败：${result.error}`;

  // 实际实现需要调用通知组件
  console.log(`[SyncToast] ${message}`);

  // 2 秒后消失（如果是成功）
  if (result.success) {
    setTimeout(() => {
      console.log('[SyncToast] Dismissed');
    }, 2000);
  }
}

/**
 * 处理保存事件
 */
export function onFileSave(filePath: string, content: string, options: SyncOptions): void {
  if (!options.on_save) {
    return;
  }

  autoSyncFile(filePath, content, options).then(result => {
    if (options.show_notifications) {
      showSyncToast(result);
    }
  });
}