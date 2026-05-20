/**
 * useTheme - 配色风格控制 Composable
 *
 * 功能:
 * - 提供主题应用的响应式方法
 * - 封装 token 更新的逻辑
 */

import { useThemeStore } from '@/stores/themeStore'

export function useTheme() {
  const store = useThemeStore()

  /**
   * 应用一组 tokens 到 CSS 变量
   * @param {Object} tokens - { '--color-primary': '#ff0000', ... }
   */
  function applyTokens(tokens) {
    const root = document.documentElement
    Object.entries(tokens).forEach(([token, value]) => {
      root.style.setProperty(token, value)
    })
  }

  /**
   * 更新单个 token 并实时预览
   * @param {string} token - CSS 变量名，如 '--color-primary'
   * @param {string} value - 新的值
   */
  function updateToken(token, value) {
    store.updateToken(token, value)
  }

  /**
   * 重置单个 token 到默认值
   * @param {string} token - CSS 变量名
   */
  function resetToken(token) {
    store.resetToken(token)
  }

  /**
   * 重置所有 tokens 到默认值
   */
  function resetAllTokens() {
    store.resetAllTokens()
  }

  /**
   * 保存当前配置
   */
  function saveTokens() {
    store.saveTokens()
  }

  /**
   * 导出当前配置为 JSON
   */
  function exportTokens() {
    return store.exportConfig()
  }

  /**
   * 导入配置
   * @param {Object} config - 导出时得到的配置对象
   */
  function importTokens(config) {
    return store.importConfig(config)
  }

  /**
   * 应用所有已保存的自定义 tokens（页面初始化时调用）
   */
  function initializeTheme() {
    store.applyAllTokens()
  }

  return {
    // State
    customTokens: store.customTokens,
    isDirty: store.isDirty,
    hasCustomConfig: store.hasCustomConfig,
    tokenGroups: store.tokenGroups,

    // Methods
    applyTokens,
    updateToken,
    resetToken,
    resetAllTokens,
    saveTokens,
    exportTokens,
    importTokens,
    initializeTheme,

    // Store 直接暴露的方法
    getDefaultValue: store.getDefaultValue,

    // Preset themes
    getPresetThemes: store.getPresetThemes,
    applyPresetTheme: store.applyPresetTheme,
    getActivePresetId: store.getActivePresetId
  }
}