/**
 * Path Filter - 处理 raw/ 目录和路径过滤规则
 */

export enum PathFilterMode {
  STRICT = 'strict',           // 默认：不含 raw/
  INCLUDE_RAW = 'include_raw', // 完全共享模式：含 raw/
}

/**
 * 检查文件路径是否应被包含
 */
export function shouldIncludePath(
  path: string,
  mode: PathFilterMode = PathFilterMode.STRICT
): boolean {
  if (mode === PathFilterMode.STRICT) {
    // 默认模式：跳过 raw/ 目录
    if (path.startsWith('raw/') || path.startsWith('raw\\')) {
      return false;
    }
  }
  return true;
}

/**
 * 为同步到团队 Space 的文件添加来源标记
 */
export interface FileMetadata {
  path: string;
  frontMatter?: Record<string, unknown>;
  content?: string;
}

export function addSourceMarker(
  file: FileMetadata,
  userId: string,
  source: 'personal' | 'raw' | 'shared'
): FileMetadata {
  const frontMatter = file.frontMatter ? { ...file.frontMatter } : {};

  if (source === 'raw') {
    frontMatter['source'] = `from_raw_of_${userId}`;
  } else if (source === 'personal') {
    frontMatter['source'] = `personal_${userId}`;
  } else {
    frontMatter['source'] = `shared_${userId}`;
  }

  frontMatter['synced_at'] = new Date().toISOString();
  frontMatter['original_owner'] = userId;

  return {
    ...file,
    frontMatter,
  };
}

/**
 * 规范化路径（处理不同操作系统的路径分隔符）
 */
export function normalizePath(path: string): string {
  return path.replace(/\\/g, '/').replace(/\/+/g, '/');
}

/**
 * 检查路径是否在 Vault 根目录下
 */
export function isUnderVaultRoot(path: string, vaultRoot: string): boolean {
  const normalizedPath = normalizePath(path);
  const normalizedRoot = normalizePath(vaultRoot);
  return normalizedPath.startsWith(normalizedRoot);
}