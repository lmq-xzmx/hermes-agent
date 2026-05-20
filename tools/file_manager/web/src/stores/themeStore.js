/**
 * Theme Store - 配色风格状态管理
 *
 * 功能:
 * - 管理自定义 CSS tokens
 * - 持久化到 localStorage
 * - 提供 token 更新、重置、导出接口
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const STORAGE_KEY = 'theme_custom_tokens'
const PRESET_THEMES = {
  'apple-blue': {
    name: 'Apple 蓝',
    icon: 'palette',
    tokens: {
      '--color-primary': '#0066cc',
      '--color-primary-focus': '#0071e3',
      '--color-primary-on-dark': '#2997ff',
      '--color-secondary': '#86868b',
      '--color-secondary-hover': '#6e6e73',
      '--color-canvas': '#ffffff',
      '--color-canvas-parchment': '#f5f5f7',
      '--color-surface-pearl': '#fafafc',
      '--color-surface-tile-1': '#272729',
      '--color-surface-tile-2': '#2a2a2c',
      '--color-surface-tile-3': '#252527',
      '--color-surface-black': '#000000',
      '--color-ink': '#1d1d1f',
      '--color-body': '#1d1d1f',
      '--color-body-on-dark': '#ffffff',
      '--color-body-muted': '#cccccc',
      '--color-ink-muted-80': '#333333',
      '--color-ink-muted-48': '#7a7a7a',
      '--color-hairline': '#e0e0e0',
      '--color-divider-soft': '#f0f0f0',
      '--color-border-on-dark': 'rgba(255, 255, 255, 0.1)',
      '--color-border-on-dark-soft': 'rgba(255, 255, 255, 0.08)',
      '--color-success': '#34c759',
      '--color-warning': '#ff9500',
      '--color-danger': '#ff3b30',
      '--color-success-subtle': 'rgba(52, 199, 89, 0.15)',
      '--color-warning-subtle': 'rgba(255, 149, 0, 0.15)',
      '--color-danger-subtle': 'rgba(255, 59, 48, 0.15)',
      '--shadow-sm': '0 1px 3px rgba(0, 0, 0, 0.08)',
      '--shadow-md': '0 4px 12px rgba(0, 0, 0, 0.1)',
      '--shadow-lg': '0 8px 24px rgba(0, 0, 0, 0.12)',
    }
  },
  'warm-orange': {
    name: '活力橙',
    icon: 'sun',
    tokens: {
      '--color-primary': '#f97316',
      '--color-primary-focus': '#ea580c',
      '--color-primary-on-dark': '#fb923c',
      '--color-secondary': '#86868b',
      '--color-secondary-hover': '#6e6e73',
      '--color-canvas': '#ffffff',
      '--color-canvas-parchment': '#fafafa',
      '--color-surface-pearl': '#f5f5f7',
      '--color-surface-tile-1': '#1d1d1f',
      '--color-surface-tile-2': '#2a2a2c',
      '--color-surface-tile-3': '#3a3a3c',
      '--color-surface-black': '#000000',
      '--color-ink': '#1d1d1f',
      '--color-body': '#1d1d1f',
      '--color-body-on-dark': '#ffffff',
      '--color-body-muted': '#cccccc',
      '--color-ink-muted-80': '#333333',
      '--color-ink-muted-48': '#7a7a7a',
      '--color-hairline': '#e0e0e0',
      '--color-divider-soft': '#f0f0f0',
      '--color-border-on-dark': 'rgba(255, 255, 255, 0.1)',
      '--color-border-on-dark-soft': 'rgba(255, 255, 255, 0.08)',
      '--color-success': '#34c759',
      '--color-warning': '#ff9500',
      '--color-danger': '#ff3b30',
      '--color-success-subtle': 'rgba(52, 199, 89, 0.15)',
      '--color-warning-subtle': 'rgba(255, 149, 0, 0.15)',
      '--color-danger-subtle': 'rgba(255, 59, 48, 0.15)',
      '--shadow-sm': '0 1px 3px rgba(0, 0, 0, 0.08)',
      '--shadow-md': '0 4px 12px rgba(0, 0, 0, 0.1)',
      '--shadow-lg': '0 8px 24px rgba(0, 0, 0, 0.12)',
    }
  },
  'fresh-green': {
    name: '清新绿',
    icon: 'leaf',
    tokens: {
      '--color-primary': '#10b981',
      '--color-primary-focus': '#059669',
      '--color-primary-on-dark': '#34d399',
      '--color-secondary': '#86868b',
      '--color-secondary-hover': '#6e6e73',
      '--color-canvas': '#ffffff',
      '--color-canvas-parchment': '#f0fdf4',
      '--color-surface-pearl': '#f5f5f7',
      '--color-surface-tile-1': '#272729',
      '--color-surface-tile-2': '#2a2a2c',
      '--color-surface-tile-3': '#252527',
      '--color-surface-black': '#000000',
      '--color-ink': '#1d1d1f',
      '--color-body': '#1d1d1f',
      '--color-body-on-dark': '#ffffff',
      '--color-body-muted': '#cccccc',
      '--color-ink-muted-80': '#333333',
      '--color-ink-muted-48': '#7a7a7a',
      '--color-hairline': '#e0e0e0',
      '--color-divider-soft': '#f0f0f0',
      '--color-border-on-dark': 'rgba(255, 255, 255, 0.1)',
      '--color-border-on-dark-soft': 'rgba(255, 255, 255, 0.08)',
      '--color-success': '#34c759',
      '--color-warning': '#ff9500',
      '--color-danger': '#ff3b30',
      '--color-success-subtle': 'rgba(52, 199, 89, 0.15)',
      '--color-warning-subtle': 'rgba(255, 149, 0, 0.15)',
      '--color-danger-subtle': 'rgba(255, 59, 48, 0.15)',
      '--shadow-sm': '0 1px 3px rgba(0, 0, 0, 0.08)',
      '--shadow-md': '0 4px 12px rgba(0, 0, 0, 0.1)',
      '--shadow-lg': '0 8px 24px rgba(0, 0, 0, 0.12)',
    }
  },
  'purple': {
    name: '薰衣草紫',
    icon: 'sparkles',
    tokens: {
      '--color-primary': '#8b5cf6',
      '--color-primary-focus': '#7c3aed',
      '--color-primary-on-dark': '#a78bfa',
      '--color-secondary': '#86868b',
      '--color-secondary-hover': '#6e6e73',
      '--color-canvas': '#ffffff',
      '--color-canvas-parchment': '#faf5ff',
      '--color-surface-pearl': '#f5f5f7',
      '--color-surface-tile-1': '#272729',
      '--color-surface-tile-2': '#2a2a2c',
      '--color-surface-tile-3': '#252527',
      '--color-surface-black': '#000000',
      '--color-ink': '#1d1d1f',
      '--color-body': '#1d1d1f',
      '--color-body-on-dark': '#ffffff',
      '--color-body-muted': '#cccccc',
      '--color-ink-muted-80': '#333333',
      '--color-ink-muted-48': '#7a7a7a',
      '--color-hairline': '#e0e0e0',
      '--color-divider-soft': '#f0f0f0',
      '--color-border-on-dark': 'rgba(255, 255, 255, 0.1)',
      '--color-border-on-dark-soft': 'rgba(255, 255, 255, 0.08)',
      '--color-success': '#34c759',
      '--color-warning': '#ff9500',
      '--color-danger': '#ff3b30',
      '--color-success-subtle': 'rgba(52, 199, 89, 0.15)',
      '--color-warning-subtle': 'rgba(255, 149, 0, 0.15)',
      '--color-danger-subtle': 'rgba(255, 59, 48, 0.15)',
      '--shadow-sm': '0 1px 3px rgba(0, 0, 0, 0.08)',
      '--shadow-md': '0 4px 12px rgba(0, 0, 0, 0.1)',
      '--shadow-lg': '0 8px 24px rgba(0, 0, 0, 0.12)',
    }
  },
  'neutral-gray': {
    name: '中性灰',
    icon: 'circle',
    tokens: {
      '--color-primary': '#6b7280',
      '--color-primary-focus': '#4b5563',
      '--color-primary-on-dark': '#9ca3af',
      '--color-secondary': '#86868b',
      '--color-secondary-hover': '#6e6e73',
      '--color-canvas': '#ffffff',
      '--color-canvas-parchment': '#f9f9f9',
      '--color-surface-pearl': '#f5f5f7',
      '--color-surface-tile-1': '#272729',
      '--color-surface-tile-2': '#2a2a2c',
      '--color-surface-tile-3': '#252527',
      '--color-surface-black': '#000000',
      '--color-ink': '#1d1d1f',
      '--color-body': '#1d1d1f',
      '--color-body-on-dark': '#ffffff',
      '--color-body-muted': '#cccccc',
      '--color-ink-muted-80': '#333333',
      '--color-ink-muted-48': '#7a7a7a',
      '--color-hairline': '#e0e0e0',
      '--color-divider-soft': '#f0f0f0',
      '--color-border-on-dark': 'rgba(255, 255, 255, 0.1)',
      '--color-border-on-dark-soft': 'rgba(255, 255, 255, 0.08)',
      '--color-success': '#34c759',
      '--color-warning': '#ff9500',
      '--color-danger': '#ff3b30',
      '--color-success-subtle': 'rgba(52, 199, 89, 0.15)',
      '--color-warning-subtle': 'rgba(255, 149, 0, 0.15)',
      '--color-danger-subtle': 'rgba(255, 59, 48, 0.15)',
      '--shadow-sm': '0 1px 3px rgba(0, 0, 0, 0.08)',
      '--shadow-md': '0 4px 12px rgba(0, 0, 0, 0.1)',
      '--shadow-lg': '0 8px 24px rgba(0, 0, 0, 0.12)',
    }
  }
}
const DEFAULT_TOKEN_GROUPS = {
  brand: [
    '--color-primary',
    '--color-primary-focus',
    '--color-primary-on-dark',
    '--color-secondary',
    '--color-secondary-hover',
  ],
  surface: [
    '--color-canvas',
    '--color-canvas-parchment',
    '--color-surface-pearl',
    '--color-surface-tile-1',
    '--color-surface-tile-2',
    '--color-surface-tile-3',
    '--color-surface-black',
  ],
  text: [
    '--color-ink',
    '--color-body',
    '--color-body-on-dark',
    '--color-body-muted',
    '--color-ink-muted-80',
    '--color-ink-muted-48',
  ],
  border: [
    '--color-hairline',
    '--color-divider-soft',
    '--color-border-on-dark',
    '--color-border-on-dark-soft',
  ],
  status: [
    '--color-success',
    '--color-warning',
    '--color-danger',
    '--color-success-subtle',
    '--color-warning-subtle',
    '--color-danger-subtle',
  ],
  shadow: [
    '--shadow-sm',
    '--shadow-md',
    '--shadow-lg',
  ]
}

function loadFromStorage() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : {}
  } catch {
    return {}
  }
}

function saveToStorage(tokens) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(tokens))
  } catch (e) {
    console.warn('Failed to save theme tokens:', e)
  }
}

export const useThemeStore = defineStore('theme', () => {
  // 自定义 tokens
  const customTokens = ref(loadFromStorage())

  // 是否已修改（未保存）
  const isDirty = ref(false)

  // 是否有自定义配置
  const hasCustomConfig = computed(() => Object.keys(customTokens.value).length > 0)

  // 获取所有可调整的 token 列表（带分类）
  const tokenGroups = computed(() => {
    if (!DEFAULT_TOKEN_GROUPS) return {}
    const groups = {}
    for (const [groupName, tokens] of Object.entries(DEFAULT_TOKEN_GROUPS)) {
      if (!tokens) continue
      groups[groupName] = tokens.map(token => ({
        token,
        value: getComputedValue(token),
        isModified: token in customTokens.value
      }))
    }
    return groups
  })

  // 获取当前生效的 token 值
  function getComputedValue(token) {
    if (token in customTokens.value) {
      return customTokens.value[token]
    }
    // 从 CSS 变量获取默认值
    return getComputedStyle(document.documentElement).getPropertyValue(token).trim()
  }

  // 更新单个 token
  function updateToken(token, value) {
    if (value === getDefaultValue(token)) {
      // 如果值等于默认值，移除自定义
      delete customTokens.value[token]
    } else {
      customTokens.value[token] = value
    }
    isDirty.value = true

    // 立即应用到 CSS 变量（实时预览）
    document.documentElement.style.setProperty(token, value)
  }

  // 获取 token 的默认值
  function getDefaultValue(token) {
    const defaults = {
      '--color-primary': '#0066cc',
      '--color-primary-focus': '#0071e3',
      '--color-primary-on-dark': '#2997ff',
      '--color-secondary': '#86868b',
      '--color-secondary-hover': '#6e6e73',
      '--color-success': '#34c759',
      '--color-warning': '#ff9500',
      '--color-danger': '#ff3b30',
      '--color-canvas': '#ffffff',
      '--color-canvas-parchment': '#f5f5f7',
      '--color-surface-pearl': '#fafafc',
      '--color-surface-tile-1': '#272729',
      '--color-surface-tile-2': '#2a2a2c',
      '--color-surface-tile-3': '#252527',
      '--color-surface-black': '#000000',
      '--color-ink': '#1d1d1f',
      '--color-body': '#1d1d1f',
      '--color-body-on-dark': '#ffffff',
      '--color-body-muted': '#cccccc',
      '--color-ink-muted-80': '#333333',
      '--color-ink-muted-48': '#7a7a7a',
      '--color-hairline': '#e0e0e0',
      '--color-divider-soft': '#f0f0f0',
      '--color-border-on-dark': 'rgba(255, 255, 255, 0.1)',
      '--color-border-on-dark-soft': 'rgba(255, 255, 255, 0.08)',
      '--color-success-subtle': 'rgba(52, 199, 89, 0.15)',
      '--color-warning-subtle': 'rgba(255, 149, 0, 0.15)',
      '--color-danger-subtle': 'rgba(255, 59, 48, 0.15)',
      '--shadow-sm': '0 1px 3px rgba(0, 0, 0, 0.08)',
      '--shadow-md': '0 4px 12px rgba(0, 0, 0, 0.1)',
      '--shadow-lg': '0 8px 24px rgba(0, 0, 0, 0.12)',
    }
    return defaults[token] || ''
  }

  // 重置单个 token 到默认值
  function resetToken(token) {
    if (token in customTokens.value) {
      delete customTokens.value[token]
      document.documentElement.style.setProperty(token, getDefaultValue(token))
    }
    isDirty.value = true
  }

  // 重置所有 tokens 到默认值
  function resetAllTokens() {
    const tokensToReset = [...Object.keys(customTokens.value)]
    customTokens.value = {}
    tokensToReset.forEach(token => {
      document.documentElement.style.setProperty(token, getDefaultValue(token))
    })
    isDirty.value = false
    saveToStorage({})
  }

  // 保存配置到 localStorage
  function saveTokens() {
    saveToStorage(customTokens.value)
    isDirty.value = false
  }

  // 应用所有自定义 tokens（页面加载时调用）
  function applyAllTokens() {
    Object.entries(customTokens.value).forEach(([token, value]) => {
      document.documentElement.style.setProperty(token, value)
    })
  }

  // 导出当前配置
  function exportConfig() {
    return {
      version: 1,
      timestamp: Date.now(),
      tokens: { ...customTokens.value }
    }
  }

  // 导入配置
  function importConfig(config) {
    if (!config || !config.tokens) return false
    try {
      customTokens.value = { ...config.tokens }
      applyAllTokens()
      isDirty.value = true
      return true
    } catch {
      return false
    }
  }

  // 获取所有预设主题
  function getPresetThemes() {
    return PRESET_THEMES
  }

  // 应用预设主题
  function applyPresetTheme(themeId) {
    const preset = PRESET_THEMES[themeId]
    if (!preset) return false

    try {
      // 清空当前自定义 tokens
      const tokensToReset = [...Object.keys(customTokens.value)]
      customTokens.value = {}
      tokensToReset.forEach(token => {
        document.documentElement.style.setProperty(token, getDefaultValue(token))
      })

      // 应用预设主题的 tokens
      Object.entries(preset.tokens).forEach(([token, value]) => {
        customTokens.value[token] = value
        document.documentElement.style.setProperty(token, value)
      })

      // 保存到 localStorage
      saveToStorage(customTokens.value)
      isDirty.value = false
      return true
    } catch (e) {
      console.warn('Failed to apply preset theme:', e)
      return false
    }
  }

  // 获取当前激活的预设主题 ID（如果有）
  function getActivePresetId() {
    // 如果所有 customTokens 都匹配某个预设主题，则返回该预设主题 ID
    for (const [id, preset] of Object.entries(PRESET_THEMES)) {
      const presetTokens = preset.tokens
      const customKeys = Object.keys(customTokens.value)

      // 检查所有自定义 token 是否都匹配预设
      if (customKeys.length > 0 && customKeys.every(key => customTokens.value[key] === presetTokens[key])) {
        return id
      }
    }
    // 默认返回活力橙
    return 'warm-orange'
  }

  return {
    // State
    customTokens,
    isDirty,
    hasCustomConfig,

    // Getters
    tokenGroups,

    // Actions
    updateToken,
    resetToken,
    resetAllTokens,
    saveTokens,
    applyAllTokens,
    exportConfig,
    importConfig,
    getDefaultValue,
    getPresetThemes,
    applyPresetTheme,
    getActivePresetId
  }
})