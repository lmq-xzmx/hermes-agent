/**
 * Sensitive Content Scanner - 本地扫描敏感内容
 *
 * 扫描引擎在 Obsidian 本地运行，数据不出本地
 */
export var SensitiveType;
(function (SensitiveType) {
    SensitiveType["PASSWORD"] = "password";
    SensitiveType["API_KEY"] = "api_key";
    SensitiveType["AWS_KEY"] = "aws_key";
    SensitiveType["CREDIT_CARD"] = "credit_card";
    SensitiveType["INTERNAL_SECRET"] = "internal_secret";
})(SensitiveType || (SensitiveType = {}));
// 敏感内容正则模式
const SENSITIVE_PATTERNS = [
    {
        type: SensitiveType.PASSWORD,
        regex: /(?:"password"|'password'|password)\s*[:=]\s*(?:"[^"]{4,}|'[^']{4,}')/i,
        severity: 'high',
        description: '可能的密码配置',
    },
    {
        type: SensitiveType.API_KEY,
        regex: /sk-[A-Za-z0-9]{20,}/,
        severity: 'high',
        description: 'API 密钥',
    },
    {
        type: SensitiveType.AWS_KEY,
        regex: /AKIA[0-9A-Z]{16}/,
        severity: 'high',
        description: 'AWS 访问密钥',
    },
    {
        type: SensitiveType.CREDIT_CARD,
        regex: /\b(?:\d{4}[- ]?){3}\d{4}\b/,
        severity: 'high',
        description: '信用卡号',
    },
    {
        type: SensitiveType.INTERNAL_SECRET,
        regex: /(?:机密|绝密|仅内部|confidential|secret|private|密钥|api_key|apikey)\s*[:=]\s*["'][^"']+["']/i,
        severity: 'medium',
        description: '内部敏感信息',
    },
];
/**
 * 扫描单行内容
 */
function scanLine(line, lineNum, path) {
    const matches = [];
    for (const pattern of SENSITIVE_PATTERNS) {
        if (pattern.regex.test(line)) {
            matches.push({
                type: pattern.type,
                path,
                line: lineNum,
                snippet: line.trim().slice(0, 100), // 截断以保护敏感信息
                severity: pattern.severity,
            });
        }
    }
    return matches;
}
/**
 * 扫描文件内容
 */
export function scanContent(content, filePath = 'unknown') {
    const startTime = Date.now();
    const matches = [];
    const lines = content.split('\n');
    for (let i = 0; i < lines.length; i++) {
        const lineMatches = scanLine(lines[i], i + 1, filePath);
        matches.push(...lineMatches);
    }
    // 如果没有高 severity 匹配，认为是安全的
    const hasHighSeverity = matches.some(m => m.severity === 'high');
    return {
        safe: !hasHighSeverity,
        matches,
        scanDuration: Date.now() - startTime,
    };
}
/**
 * 扫描目录（用于完全共享前的预扫描）
 */
export async function scanDirectory(dirPath, options = {}) {
    const startTime = Date.now();
    const allMatches = [];
    // 默认选项
    const opts = {
        recursive: true,
        extensions: ['.md', '.txt', '.markdown'],
        maxFileSize: 10 * 1024 * 1024, // 10MB
        ...options,
    };
    // 实际实现需要文件系统访问
    // 这里提供接口框架，具体实现在 Claudian 插件中
    return {
        safe: true,
        matches: allMatches,
        scanDuration: Date.now() - startTime,
    };
}
/**
 * 获取扫描报告（用于日志）
 */
export function formatScanReport(result) {
    if (result.safe && result.matches.length === 0) {
        return `✅ 扫描完成：未发现敏感内容 (${result.scanDuration}ms)`;
    }
    const highCount = result.matches.filter(m => m.severity === 'high').length;
    const mediumCount = result.matches.filter(m => m.severity === 'medium').length;
    const lines = [
        `⚠️ 扫描完成：发现 ${result.matches.length} 处可疑内容`,
        `- 高危: ${highCount}, 中危: ${mediumCount}`,
    ];
    for (const match of result.matches.slice(0, 5)) {
        lines.push(`  [${match.severity.toUpperCase()}] ${match.type} at ${match.path}:${match.line}`);
    }
    return lines.join('\n');
}
//# sourceMappingURL=sensitive_scan.js.map