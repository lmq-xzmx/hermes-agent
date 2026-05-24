/**
 * Path Filter - 处理 raw/ 目录和路径过滤规则
 */
export var PathFilterMode;
(function (PathFilterMode) {
    PathFilterMode["STRICT"] = "strict";
    PathFilterMode["INCLUDE_RAW"] = "include_raw";
})(PathFilterMode || (PathFilterMode = {}));
/**
 * 检查文件路径是否应被包含
 */
export function shouldIncludePath(path, mode = PathFilterMode.STRICT) {
    if (mode === PathFilterMode.STRICT) {
        // 默认模式：跳过 raw/ 目录
        if (path.startsWith('raw/') || path.startsWith('raw\\')) {
            return false;
        }
    }
    return true;
}
export function addSourceMarker(file, userId, source) {
    const frontMatter = file.frontMatter ? { ...file.frontMatter } : {};
    if (source === 'raw') {
        frontMatter['source'] = `from_raw_of_${userId}`;
    }
    else if (source === 'personal') {
        frontMatter['source'] = `personal_${userId}`;
    }
    else {
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
export function normalizePath(path) {
    return path.replace(/\\/g, '/').replace(/\/+/g, '/');
}
/**
 * 检查路径是否在 Vault 根目录下
 */
export function isUnderVaultRoot(path, vaultRoot) {
    const normalizedPath = normalizePath(path);
    const normalizedRoot = normalizePath(vaultRoot);
    return normalizedPath.startsWith(normalizedRoot);
}
//# sourceMappingURL=path_filter.js.map