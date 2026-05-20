<template>
  <Modal v-model="isOpen" title="🎨 配色风格调整" size="xl" :closable="true">
    <!-- Preset Themes -->
    <div class="theme-panel__presets">
      <button
        v-for="(preset, id) in presetThemes"
        :key="id"
        class="theme-panel__preset-btn"
        :class="{ 'theme-panel__preset-btn--active': activePresetId === id }"
        @click="handleApplyPreset(id)"
      >
        <span
          class="theme-panel__preset-swatch"
          :style="{ background: preset.tokens['--color-primary'] }"
        ></span>
        <span class="theme-panel__preset-name">{{ preset.name }}</span>
      </button>
    </div>

    <!-- Category Tabs -->
    <div class="theme-panel__tabs">
      <button
        v-for="(group, key) in safeTokenGroups"
        :key="key"
        class="theme-panel__tab"
        :class="{ 'theme-panel__tab--active': activeTab === key }"
        @click="activeTab = key"
      >
        {{ tabLabels[key] }}
        <span class="theme-panel__tab-count">{{ group.length }}</span>
      </button>
    </div>

    <!-- Token List -->
    <div class="theme-panel__content">
      <div class="theme-panel__token-list">
        <ColorPicker
          v-for="item in currentGroupItems"
          :key="item.token"
          :token="item.token"
          :model-value="item.value"
          :default-value="getDefaultValue(item.token)"
          @update:model-value="(v) => updateToken(item.token, v)"
          @reset="handleResetToken"
        />
      </div>

      <!-- Live Preview -->
      <div class="theme-panel__preview">
        <h4 class="theme-panel__preview-title">实时预览</h4>
        <div class="theme-panel__preview-content">
          <!-- Buttons -->
          <div class="theme-panel__preview-row">
            <button class="btn-apple-primary">主按钮</button>
            <button class="btn-apple-secondary">次按钮</button>
            <button class="btn-apple-danger">危险按钮</button>
          </div>

          <!-- Card -->
          <div class="theme-panel__preview-card">
            <div class="theme-panel__preview-card-header">卡片标题</div>
            <p class="theme-panel__preview-card-body">
              这是一段示例文字，用于预览配色效果。当前主题会实时应用所有颜色变化。
            </p>
          </div>

          <!-- Input -->
          <div class="theme-panel__preview-input">
            <input
              type="text"
              class="apple-input"
              placeholder="输入框示例"
              value="预览文字"
            />
          </div>

          <!-- Status Badges -->
          <div class="theme-panel__preview-row">
            <span class="badge-success">成功</span>
            <span class="badge-warning">警告</span>
            <span class="badge-danger">危险</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <template #footer>
      <div class="theme-panel__footer">
        <button class="btn-apple-secondary" @click="handleResetAll">
          恢复默认
        </button>
        <div class="theme-panel__footer-right">
          <button class="btn-apple-secondary" @click="handleExport">
            导出配置
          </button>
          <button class="btn-apple-primary" @click="handleSave">
            保存配置
          </button>
        </div>
      </div>
    </template>
  </Modal>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useThemeStore } from '@/stores/themeStore'
import { useTheme } from '@/composables/useTheme'
import Modal from './Modal.vue'
import ColorPicker from './ColorPicker.vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue', 'saved', 'reset'])

const {
  tokenGroups,
  updateToken,
  resetToken,
  resetAllTokens,
  saveTokens,
  exportTokens,
  getDefaultValue,
  getPresetThemes,
  applyPresetTheme,
  getActivePresetId
} = useTheme()

// Preset themes
const presetThemes = getPresetThemes()
const activePresetId = ref(getActivePresetId())

// Apply preset theme
function handleApplyPreset(themeId) {
  applyPresetTheme(themeId)
  activePresetId.value = themeId
}

// Safe tokenGroups wrapper
const safeTokenGroups = computed(() => {
  if (!tokenGroups) return {}
  if (typeof tokenGroups === 'object' && !('value' in tokenGroups)) return tokenGroups
  return tokenGroups.value || {}
})

// Modal visibility
const isOpen = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

// Apply preset when modal opens (if no custom config)
const themeStore = useThemeStore()
watch(isOpen, (newVal) => {
  if (newVal && !themeStore.hasCustomConfig) {
    // Auto-apply warm-orange preset on first open
    handleApplyPreset('warm-orange')
  }
})

// Tab labels
const tabLabels = {
  brand: '品牌色',
  surface: '表面色',
  text: '文字色',
  border: '边框色',
  status: '状态色',
  shadow: '阴影'
}

// Active tab
const activeTab = ref('brand')

// Current tab items
const currentGroupItems = computed(() => {
  const groups = safeTokenGroups.value
  if (!groups) return []
  return groups[activeTab.value] || []
})

// Event handlers
function handleResetToken(token) {
  resetToken(token)
}

function handleResetAll() {
  if (confirm('确定要恢复所有颜色的默认值吗？')) {
    resetAllTokens()
    emit('reset')
  }
}

function handleSave() {
  saveTokens()
  emit('saved')
  isOpen.value = false
}

function handleExport() {
  const config = exportTokens()
  const json = JSON.stringify(config, null, 2)
  navigator.clipboard.writeText(json).then(() => {
    alert('配置已复制到剪贴板')
  }).catch(() => {
    // Fallback: 打开新窗口显示 JSON
    const win = window.open('', '_blank')
    win.document.write(`<pre>${json}</pre>`)
  })
}
</script>

<style scoped>
/* =============================================
   ThemePanel - 配色风格调整面板
   ============================================= */

/* ---- Preset Themes ---- */
.theme-panel__presets {
  /* Layout */
  display: flex;
  gap: var(--space-sm);
  flex-wrap: wrap;

  /* Box Model */
  margin-bottom: var(--space-md);
  padding-bottom: var(--space-md);

  /* Visual */
  border-bottom: 1px solid var(--color-hairline);
}

.theme-panel__preset-btn {
  /* Layout */
  display: flex;
  align-items: center;
  gap: var(--space-xxs);

  /* Box Model */
  padding: var(--spacing-sm) var(--space-md);

  /* Visual */
  background: var(--color-canvas-parchment);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  color: var(--color-ink);
  font: var(--text-caption);
  cursor: pointer;

  /* Transition */
  transition: all 0.15s ease;
}

.theme-panel__preset-btn:hover {
  /* Visual */
  background: var(--color-surface-pearl);
  border-color: var(--color-ink-muted-48);
}

.theme-panel__preset-btn--active {
  /* Visual */
  background: var(--color-ink);
  color: var(--color-body-on-dark);
  border-color: var(--color-ink);
}

.theme-panel__preset-btn--active:hover {
  /* Visual */
  background: var(--color-ink);
  border-color: var(--color-ink);
}

.theme-panel__preset-swatch {
  /* Layout */
  display: inline-block;
  flex-shrink: 0;

  /* Box Model */
  width: 14px;
  height: 14px;
  border-radius: var(--radius-full);

  /* Visual */
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.theme-panel__preset-name {
  /* Typography */
  font-size: 12px;
  font-weight: 500;
}

/* ---- Tabs ---- */
.theme-panel__tabs {
  /* Layout */
  display: flex;
  gap: var(--space-xs);
  flex-wrap: wrap;

  /* Box Model */
  padding-bottom: var(--space-md);
  margin-bottom: var(--space-md);

  /* Visual */
  border-bottom: 1px solid var(--color-hairline);
}

.theme-panel__tab {
  /* Layout */
  display: flex;
  align-items: center;
  gap: var(--space-xxs);

  /* Box Model */
  padding: var(--spacing-sm) var(--space-md);

  /* Visual */
  background: none;
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  color: var(--color-ink-muted-48);
  font: var(--text-caption);
  cursor: pointer;

  /* Transition */
  transition: all 0.15s ease;
}

.theme-panel__tab:hover {
  /* Visual */
  background: var(--color-canvas-parchment);
  color: var(--color-ink);
}

.theme-panel__tab--active {
  /* Visual */
  background: var(--color-ink);
  color: var(--color-body-on-dark);
  border-color: var(--color-ink);
}

.theme-panel__tab-count {
  /* Layout */
  display: inline-flex;
  align-items: center;
  justify-content: center;

  /* Box Model */
  min-width: 18px;
  height: 18px;
  padding: 0 var(--spacing-xxs);

  /* Visual */
  background: rgba(255, 255, 255, 0.2);
  border-radius: var(--radius-full);
  font-size: 11px;
}

.theme-panel__tab:not(.theme-panel__tab--active) .theme-panel__tab-count {
  /* Visual */
  background: var(--color-canvas-parchment);
}

/* ---- Content ---- */
.theme-panel__content {
  /* Layout */
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: var(--space-lg);

  /* Box Model */
  max-height: 60vh;
  overflow: hidden;
}

.theme-panel__token-list {
  /* Layout */
  overflow-y: auto;

  /* Box Model */
  padding-right: var(--space-sm);

  /* Visual */
  background: var(--color-canvas-parchment);
  border-radius: var(--radius-lg);
}

/* ---- Preview ---- */
.theme-panel__preview {
  /* Layout */
  display: flex;
  flex-direction: column;
  gap: var(--space-md);

  /* Visual */
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
}

.theme-panel__preview-title {
  /* Text */
  font: var(--text-caption-strong);
  color: var(--color-ink-muted-48);
  text-transform: uppercase;
  letter-spacing: 0.5px;

  /* Box Model */
  margin: 0;
}

.theme-panel__preview-content {
  /* Layout */
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.theme-panel__preview-row {
  /* Layout */
  display: flex;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.theme-panel__preview-card {
  /* Visual */
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  padding: var(--space-md);
}

.theme-panel__preview-card-header {
  /* Text */
  font: var(--text-body-strong);
  color: var(--color-ink);

  /* Box Model */
  margin-bottom: var(--space-xs);
}

.theme-panel__preview-card-body {
  /* Text */
  font: var(--text-caption);
  color: var(--color-ink-muted-48);

  /* Box Model */
  margin: 0;
  line-height: 1.5;
}

.theme-panel__preview-input {
  /* Layout */
  width: 100%;
}

/* ---- Footer ---- */
.theme-panel__footer {
  /* Layout */
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.theme-panel__footer-right {
  /* Layout */
  display: flex;
  gap: var(--space-sm);
}

/* =============================================
   Responsive
   ============================================= */

@media (max-width: 900px) {
  .theme-panel__content {
    /* Layout */
    grid-template-columns: 1fr;
  }

  .theme-panel__preview {
    /* Layout */
    order: -1;
  }
}
</style>