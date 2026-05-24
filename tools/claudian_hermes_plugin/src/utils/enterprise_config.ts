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

export const DEFAULT_CONFIG: EnterpriseConfig = {
  enterprise_mode: false,
  default_share_mode: 'selective_share',
  allowed_spaces: [],
  sensitive_scan_rules: 'enterprise_default',
  audit_enabled: false,
  sync: {
    mode: 'manual',
    on_save: false,
  },
  notifications: {
    show_welcome: true,
    show_tips: true,
  },
  auth: {
    method: 'manual',
    token_refresh: 'manual',
  },
};

/**
 * 从 SSO 或专用接口获取企业配置
 */
export async function loadEnterpriseConfig(): Promise<EnterpriseConfig> {
  // 实际实现：从 SSO 获取或从 Hermes 后端获取
  try {
    const baseUrl = process.env.HERMES_BASE_URL || 'http://localhost:8080';
    const token = process.env.HERMES_TOKEN || '';

    const response = await fetch(`${baseUrl}/api/v1/enterprise/config`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (response.ok) {
      const data = await response.json() as Partial<EnterpriseConfig>;
      return { ...DEFAULT_CONFIG, ...data };
    }
  } catch (error) {
    console.warn('[Claudian] Failed to load enterprise config, using defaults');
  }

  return DEFAULT_CONFIG;
}

/**
 * 应用企业配置到 Claudian（Node.js 环境使用进程级存储）
 */
const _configStore: EnterpriseConfig = { ...DEFAULT_CONFIG };

export function applyEnterpriseConfig(config: EnterpriseConfig): void {
  Object.assign(_configStore, config);

  // 应用同步配置
  if (config.sync.on_save) {
    console.log('[Claudian] Auto-sync on save enabled');
  }

  // 应用通知配置
  if (config.notifications.show_welcome) {
    console.log('[Claudian] Welcome notifications enabled');
  }
}

/**
 * 获取当前企业配置
 */
export function getCurrentConfig(): EnterpriseConfig {
  return { ..._configStore };
}

/**
 * 检查是否已初始化（用于首次启动检测）
 */
export function isInitialized(): boolean {
  return _configStore.enterprise_mode;
}

/**
 * 标记为已初始化
 */
export function markInitialized(): void {
  _configStore.enterprise_mode = true;
}

/**
 * 生成 Claudian 企业配置文件内容（用于 IT 预装）
 */
export function generateConfigFile(config: EnterpriseConfig): string {
  return JSON.stringify(config, null, 2);
}