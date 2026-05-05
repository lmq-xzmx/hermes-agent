<template>
  <div class="knowledge-view">
    <!-- Header -->
    <div class="view-header">
      <h2 class="section-title">🧠 知识库</h2>
      <div class="header-actions">
        <button class="btn-secondary-pill" @click="showSyncSettings">
          <span class="btn-icon">⚙️</span>
          同步设置
        </button>
        <button class="btn-secondary-pill" @click="openLlmWiki">
          <span class="btn-icon">📚</span>
          打开知识库
        </button>
        <button class="btn-primary" @click="checkLlmWikiStatus">
          <span class="btn-icon">🔄</span>
          检查状态
        </button>
      </div>
    </div>

    <!-- Content -->
    <div class="knowledge-content">
      <!-- Sync Status -->
      <div class="knowledge-section">
        <h3 class="subsection-title">📊 同步状态</h3>
        <div class="card-utility">
          <div class="status-grid">
            <div class="status-item">
              <span class="status-label">llm_wiki 服务</span>
              <div class="status-value-wrapper">
                <span class="status-dot" :class="serviceStatusClass"></span>
                <span class="status-value" :class="serviceStatusClass">{{ serviceStatus }}</span>
              </div>
            </div>
            <div class="status-item">
              <span class="status-label">当前模式</span>
              <span class="status-value mode">{{ syncMode }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Sync to Knowledge Base -->
      <div class="knowledge-section">
        <h3 class="subsection-title">📁 同步到知识库</h3>
        <div class="card-utility">
          <p class="section-desc">将 file_manager 中的文档同步到 llm_wiki 知识库进行加工处理。</p>

          <div class="form-field">
            <label class="form-label">选择文件或文件夹</label>
            <input
              type="text"
              v-model="syncSourcePath"
              placeholder="/path/to/sync"
              class="apple-input full-width"
            >
          </div>

          <div class="form-field">
            <label class="form-label">目标项目</label>
            <div class="select-wrapper">
              <select v-model="syncProject" class="apple-select full-width">
                <option value="default">default</option>
              </select>
              <span class="select-arrow">›</span>
            </div>
          </div>

          <button class="btn-primary" @click="syncToLlmWiki">
            <span class="btn-icon">🔄</span>
            同步到知识库
          </button>
        </div>
      </div>

      <!-- Search Knowledge Base -->
      <div class="knowledge-section">
        <h3 class="subsection-title">🔍 搜索知识库</h3>
        <div class="card-utility">
          <div class="search-wrapper">
            <div class="search-input-wrapper">
              <span class="search-icon">🔍</span>
              <input
                type="text"
                v-model="searchQuery"
                placeholder="输入搜索关键词..."
                class="search-input full-width"
              >
            </div>
            <button class="btn-secondary-pill" @click="searchKnowledge">搜索</button>
          </div>

          <div v-if="searchResults.length > 0" class="search-results">
            <div
              v-for="result in searchResults"
              :key="result.id"
              class="search-result-item"
            >
              <div class="result-icon">📄</div>
              <div class="result-content">
                <div class="result-title">{{ result.title }}</div>
                <div class="result-snippet">{{ result.snippet }}</div>
              </div>
            </div>
          </div>

          <div v-else-if="searched && searchResults.length === 0" class="empty-search">
            <div class="empty-icon">🔍</div>
            <p class="empty-text">未找到匹配结果</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../services/api.js'

const emit = defineEmits(['show-toast'])

const serviceStatus = ref('检查中...')
const syncMode = ref('-')
const syncSourcePath = ref('')
const syncProject = ref('default')
const searchQuery = ref('')
const searchResults = ref([])
const searched = ref(false)

onMounted(() => {
  checkLlmWikiStatus()
})

async function checkLlmWikiStatus() {
  serviceStatus.value = '检查中...'
  try {
    const data = await api.getKnowledgeStatus()
    serviceStatus.value = data.running ? '运行中' : '已停止'
    syncMode.value = data.sync_mode || '手动'
  } catch (err) {
    serviceStatus.value = '未知'
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

function showSyncSettings() {
  const mode = prompt('选择同步模式:\n1. manual - 手动\n2. interval - 定时同步\n3. webhook - Webhook', 'manual')
  if (!mode) return

  const modes = { '1': 'manual', '2': 'interval', '3': 'webhook' }
  const selectedMode = modes[mode] || mode

  if (selectedMode === 'interval') {
    const interval = prompt('同步间隔（分钟）:', '30')
    if (!interval) return
    localStorage.setItem('llm_sync_mode', selectedMode)
    localStorage.setItem('llm_sync_interval', interval)
    emit('show-toast', { type: 'success', title: '已保存', message: `定时同步已设置，每 ${interval} 分钟` })
  } else {
    localStorage.setItem('llm_sync_mode', selectedMode)
    const modeNames = { 'manual': '手动', 'webhook': 'Webhook' }
    emit('show-toast', { type: 'success', title: '已保存', message: `同步模式已设置为 ${modeNames[selectedMode] || selectedMode}` })
  }
}

function openLlmWiki() {
  if (window.__TAURI_INVOKE__) {
    window.__TAURI_INVOKE__('open_llm_wiki')
  } else {
    window.open('http://localhost:8080/llm_wiki', '_blank')
  }
}

async function syncToLlmWiki() {
  if (!syncSourcePath.value) {
    emit('show-toast', { type: 'error', title: '错误', message: '请输入同步路径' })
    return
  }

  try {
    await api.syncToKnowledge(syncSourcePath.value, syncProject.value)
    emit('show-toast', { type: 'success', title: '成功', message: '同步已启动' })
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

async function searchKnowledge() {
  if (!searchQuery.value) {
    emit('show-toast', { type: 'error', title: '错误', message: '请输入搜索关键词' })
    return
  }

  searched.value = true
  try {
    const data = await api.searchKnowledge(searchQuery.value, syncProject.value)
    searchResults.value = data.results || []
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

const serviceStatusClass = computed(() => ({
  'running': serviceStatus.value === '运行中',
  'stopped': serviceStatus.value === '已停止',
  'checking': serviceStatus.value === '检查中...',
  'unknown': serviceStatus.value === '未知'
}))
</script>

<style scoped>
.knowledge-view {
  flex: 1;
  overflow: auto;
  padding: var(--space-section, 80px);
  background: var(--color-canvas-parchment, #f5f5f7);
}

.view-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-xl, 32px);
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
  padding: var(--space-lg, 24px);
  background: var(--color-canvas, #ffffff);
  border-radius: var(--rounded-lg, 18px);
  border: 1px solid var(--color-hairline, #e0e0e0);
}

.header-actions {
  display: flex;
  gap: var(--space-sm, 12px);
}

.section-title {
  font: var(--text-display-lg, 600 40px/1.1 0);
  font-weight: 600;
  color: var(--color-ink, #1d1d1f);
  margin: 0;
}

.knowledge-content {
  max-width: 800px;
  margin: 0 auto;
}

.knowledge-section {
  margin-bottom: var(--space-xl, 32px);
}

.subsection-title {
  font: var(--text-body-strong, 17px/1.24 -0.374px 600);
  font-weight: 600;
  color: var(--color-ink, #1d1d1f);
  margin: 0 0 var(--space-md, 17px);
}

/* Card Utility - Apple Store Card */
.card-utility {
  background: var(--color-canvas, #ffffff);
  border: 1px solid var(--color-hairline, #e0e0e0);
  border-radius: var(--rounded-lg, 18px);
  padding: var(--space-lg, 24px);
}

.section-desc {
  font: var(--text-body, 17px/1.47 -0.374px);
  color: var(--color-ink-muted-48, #7a7a7a);
  margin-bottom: var(--space-lg, 24px);
}

/* Status Grid */
.status-grid {
  display: flex;
  gap: var(--space-xxl, 48px);
}

.status-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-xxs, 4px);
}

.status-label {
  font: var(--text-caption, 14px/1.43 -0.224px);
  color: var(--color-ink-muted-48, #7a7a7a);
  text-transform: uppercase;
  letter-spacing: -0.12px;
}

.status-value-wrapper {
  display: flex;
  align-items: center;
  gap: var(--space-sm, 12px);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot.running {
  background: #34c759;
  box-shadow: 0 0 4px #34c759;
}

.status-dot.stopped {
  background: #ff3b30;
}

.status-dot.checking {
  background: #ff9500;
  animation: pulse 1.5s ease-in-out infinite;
}

.status-dot.unknown {
  background: var(--color-ink-muted-48, #7a7a7a);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-value {
  font: var(--text-body, 17px/1.47 -0.374px);
  font-weight: 600;
}

.status-value.running { color: #34c759; }
.status-value.stopped { color: #ff3b30; }
.status-value.checking { color: #ff9500; }
.status-value.unknown { color: var(--color-ink-muted-48, #7a7a7a); }
.status-value.mode { color: var(--color-ink, #1d1d1f); font-weight: 400; }

/* Form Field */
.form-field {
  margin-bottom: var(--space-md, 17px);
}

.form-label {
  display: block;
  font: var(--text-caption, 14px/1.43 -0.224px);
  font-weight: 600;
  color: var(--color-ink, #1d1d1f);
  margin-bottom: var(--space-xxs, 4px);
}

/* Apple Input - pill style */
.apple-input {
  padding: 12px 17px;
  background: var(--color-canvas, #ffffff);
  border: 1px solid var(--color-hairline, #e0e0e0);
  border-radius: var(--radius-pill, 9999px);
  color: var(--color-ink, #1d1d1f);
  font: var(--text-body, 17px/1.47 -0.374px);
  transition: border-color 0.2s;
  height: 44px;
  box-sizing: border-box;
}

.apple-input:focus {
  outline: none;
  border-color: var(--color-primary-focus, #0071e3);
  box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.15);
}

.apple-input.full-width {
  width: 100%;
}

.apple-input::placeholder {
  color: var(--color-ink-muted-48, #7a7a7a);
}

/* Select */
.select-wrapper {
  position: relative;
}

.apple-select {
  appearance: none;
  padding: 12px 40px 12px 17px;
  background: var(--color-canvas, #ffffff);
  border: 1px solid var(--color-hairline, #e0e0e0);
  border-radius: var(--radius-pill, 9999px);
  color: var(--color-ink, #1d1d1f);
  font: var(--text-body, 17px/1.47 -0.374px);
  height: 44px;
  cursor: pointer;
  transition: border-color 0.2s;
  width: 100%;
}

.apple-select:focus {
  outline: none;
  border-color: var(--color-primary-focus, #0071e3);
  box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.15);
}

.select-arrow {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-ink-muted-48, #7a7a7a);
  font-size: 18px;
  pointer-events: none;
}

/* Buttons - Apple Pill Style */
.btn-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-xs, 8px);
  background: var(--color-primary, #0066cc);
  color: var(--color-on-primary, #ffffff);
  border: none;
  border-radius: var(--radius-pill, 9999px);
  font: var(--text-body, 17px/1.47 -0.374px);
  padding: 11px 22px;
  cursor: pointer;
  transition: transform 0.1s ease, background-color 0.2s ease;
  height: 44px;
}

.btn-primary:hover {
  background: var(--color-primary-focus, #0071e3);
}

.btn-primary:active {
  transform: scale(0.95);
}

.btn-primary:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.3);
}

.btn-secondary-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-xs, 8px);
  background: transparent;
  color: var(--color-primary, #0066cc);
  border: 1px solid var(--color-primary, #0066cc);
  border-radius: var(--radius-pill, 9999px);
  font: var(--text-body, 17px/1.47 -0.374px);
  padding: 10px 20px;
  cursor: pointer;
  transition: transform 0.1s ease, background-color 0.2s ease;
  height: 40px;
}

.btn-secondary-pill:hover {
  background: rgba(0, 102, 204, 0.08);
}

.btn-secondary-pill:active {
  transform: scale(0.95);
}

.btn-secondary-pill:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.15);
}

.btn-icon {
  font-size: 14px;
  line-height: 1;
}

/* Search */
.search-wrapper {
  display: flex;
  gap: var(--space-sm, 12px);
  align-items: center;
}

.search-input-wrapper {
  flex: 1;
  position: relative;
}

.search-icon {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 16px;
  color: var(--color-ink-muted-48, #7a7a7a);
  pointer-events: none;
}

.search-input {
  padding: 12px 20px 12px 44px;
  background: var(--color-canvas, #ffffff);
  border: 1px solid var(--color-hairline, #e0e0e0);
  border-radius: var(--radius-pill, 9999px);
  color: var(--color-ink, #1d1d1f);
  font: var(--text-body, 17px/1.47 -0.374px);
  transition: border-color 0.2s;
  height: 44px;
  box-sizing: border-box;
  width: 100%;
}

.search-input:focus {
  outline: none;
  border-color: var(--color-primary-focus, #0071e3);
  box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.15);
}

.search-input::placeholder {
  color: var(--color-ink-muted-48, #7a7a7a);
}

/* Search Results */
.search-results {
  margin-top: var(--space-lg, 24px);
  border-top: 1px solid var(--color-divider-soft, #f0f0f0);
  padding-top: var(--space-lg, 24px);
}

.search-result-item {
  display: flex;
  gap: var(--space-md, 17px);
  padding: var(--space-md, 17px) 0;
  border-bottom: 1px solid var(--color-divider-soft, #f0f0f0);
}

.search-result-item:last-child {
  border-bottom: none;
}

.result-icon {
  font-size: 24px;
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface-pearl, #fafafc);
  border-radius: var(--rounded-sm, 8px);
}

.result-content {
  flex: 1;
  min-width: 0;
}

.result-title {
  font: var(--text-body-strong, 17px/1.24 -0.374px 600);
  font-weight: 600;
  color: var(--color-primary, #0066cc);
  margin-bottom: var(--space-xxs, 4px);
}

.result-snippet {
  font: var(--text-caption, 14px/1.43 -0.224px);
  color: var(--color-ink-muted-48, #7a7a7a);
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Empty Search */
.empty-search {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-xxl, 48px);
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: var(--space-md, 17px);
  opacity: 0.5;
}

.empty-text {
  font: var(--text-body, 17px/1.47 -0.374px);
  color: var(--color-ink-muted-48, #7a7a7a);
  margin: 0;
}
</style>
