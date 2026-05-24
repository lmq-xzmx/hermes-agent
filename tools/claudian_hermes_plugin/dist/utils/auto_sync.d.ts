/**
 * Auto Sync Service - 保存即自动同步
 *
 * 监控文件变化并在保存时自动同步到团队 Space
 */
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
export declare function autoSyncFile(filePath: string, content: string, options: SyncOptions): Promise<SyncResult>;
/**
 * 显示同步状态提示（右下角）
 */
export declare function showSyncToast(result: SyncResult): void;
/**
 * 处理保存事件
 */
export declare function onFileSave(filePath: string, content: string, options: SyncOptions): void;
//# sourceMappingURL=auto_sync.d.ts.map