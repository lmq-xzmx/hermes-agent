/**
 * Sensitive Content Scanner - 本地扫描敏感内容
 *
 * 扫描引擎在 Obsidian 本地运行，数据不出本地
 */
export declare enum SensitiveType {
    PASSWORD = "password",
    API_KEY = "api_key",
    AWS_KEY = "aws_key",
    CREDIT_CARD = "credit_card",
    INTERNAL_SECRET = "internal_secret"
}
export interface SensitiveMatch {
    type: SensitiveType;
    path: string;
    line: number;
    snippet: string;
    severity: 'high' | 'medium' | 'low';
}
export interface ScanResult {
    safe: boolean;
    matches: SensitiveMatch[];
    scanDuration: number;
}
/**
 * 扫描文件内容
 */
export declare function scanContent(content: string, filePath?: string): ScanResult;
/**
 * 扫描目录（用于完全共享前的预扫描）
 */
export declare function scanDirectory(dirPath: string, options?: {
    recursive?: boolean;
    extensions?: string[];
    maxFileSize?: number;
}): Promise<ScanResult>;
/**
 * 获取扫描报告（用于日志）
 */
export declare function formatScanReport(result: ScanResult): string;
//# sourceMappingURL=sensitive_scan.d.ts.map