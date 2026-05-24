/**
 * Enterprise Config - 企业配置解析与加载
 *
 * Claudian 首次启动时自动加载企业配置
 */
export interface EnterpriseConfig {
    enterprise_mode: boolean;
    default_share_mode: 'full_share' | 'selective_share';
    allowed_spaces: string[];
    sensitive_scan_rules: 'enterprise_default' | 'strict' | 'relaxed';
    audit_enabled: boolean;
    sync: {
        mode: 'auto_incremental' | 'manual';
        on_save: boolean;
    };
    notifications: {
        show_welcome: boolean;
        show_tips: boolean;
    };
    auth: {
        method: 'sso_auto' | 'manual';
        token_refresh: 'auto' | 'manual';
    };
}
export declare const DEFAULT_CONFIG: EnterpriseConfig;
/**
 * 从 SSO 或专用接口获取企业配置
 */
export declare function loadEnterpriseConfig(): Promise<EnterpriseConfig>;
export declare function applyEnterpriseConfig(config: EnterpriseConfig): void;
/**
 * 获取当前企业配置
 */
export declare function getCurrentConfig(): EnterpriseConfig;
/**
 * 检查是否已初始化（用于首次启动检测）
 */
export declare function isInitialized(): boolean;
/**
 * 标记为已初始化
 */
export declare function markInitialized(): void;
/**
 * 生成 Claudian 企业配置文件内容（用于 IT 预装）
 */
export declare function generateConfigFile(config: EnterpriseConfig): string;
//# sourceMappingURL=enterprise_config.d.ts.map