/**
 * Path Filter - 处理 raw/ 目录和路径过滤规则
 */
export declare enum PathFilterMode {
    STRICT = "strict",// 默认：不含 raw/
    INCLUDE_RAW = "include_raw"
}
/**
 * 检查文件路径是否应被包含
 */
export declare function shouldIncludePath(path: string, mode?: PathFilterMode): boolean;
/**
 * 为同步到团队 Space 的文件添加来源标记
 */
export interface FileMetadata {
    path: string;
    frontMatter?: Record<string, unknown>;
    content?: string;
}
export declare function addSourceMarker(file: FileMetadata, userId: string, source: 'personal' | 'raw' | 'shared'): FileMetadata;
/**
 * 规范化路径（处理不同操作系统的路径分隔符）
 */
export declare function normalizePath(path: string): string;
/**
 * 检查路径是否在 Vault 根目录下
 */
export declare function isUnderVaultRoot(path: string, vaultRoot: string): boolean;
//# sourceMappingURL=path_filter.d.ts.map