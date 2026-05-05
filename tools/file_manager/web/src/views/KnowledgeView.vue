<template>
  <div class="knowledge-view">
    <!-- Header -->
    <div class="view-header">
      <h2 class="section-title">🧠 知识库</h2>
      <div class="header-actions">
        <button class="btn-apple-secondary" @click="showSyncSettings">
          <span class="btn-icon">⚙️</span>
          同步设置
        </button>
        <button class="btn-apple-secondary" @click="openLlmWiki">
          <span class="btn-icon">📚</span>
          打开知识库
        </button>
        <button class="btn-apple-primary" @click="checkLlmWikiStatus">
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

          <button class="btn-apple-primary" @click="syncToLlmWiki">
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
            <button class="btn-apple-secondary" @click="searchKnowledge">搜索</button>
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
  padding: var(--spacing-lg);
  background: var(--color-canvas-parchment);
}

.view-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-xl);
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
  padding: var(--space-lg);
  background: var(--color-canvas);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-hairline);
}

.header-actions {
  display: flex;
  gap: var(--space-sm);
}

.section-title {
  font: var(--text-display-lg);
  font-weight: 600;
  color: var(--color-ink);
  margin: 0;
}

.knowledge-content {
  max-width: 800px;
  margin: 0 auto;
}

.knowledge-section {
  margin-bottom: var(--space-xl);
}

.subsection-title {
  font: var(--text-body-strong);
  color: var(--color-ink);
  margin: 0 0 var(--space-md);
}

/* Card Utility - Apple Store Card */
.card-utility {
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--rounded-lg);
  padding: var(--space-lg);
}

.section-desc {
  font: var(--text-body);
  color: var(--color-ink-muted-48);
  margin-bottom: var(--space-lg);
}

/* Status Grid */
.status-grid {
  display: flex;
  gap: var(--space-xxl);
}

.status-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-xxs);
}

.status-label {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
  text-transform: uppercase;
  letter-spacing: -0.12px;
}

.status-value-wrapper {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.status-dot {
  width: var(--spacing-xs);
  height: var(--spacing-xs);
  border-radius: var(--radius-full);
  flex-shrink: 0;
}

.status-dot.running {
  background: var(--color-success);
}

.status-dot.stopped {
  background: var(--color-danger);
}

.status-dot.checking {
  background: var(--color-warning);
  animation: pulse 1.5s ease-in-out infinite;
}

.status-dot.unknown {
  background: var(--color-ink-muted-48);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-value {
  font: var(--text-body);
  font-weight: 600;
}

.status-value.running { color: var(--color-success); }
.status-value.stopped { color: var(--color-danger); }
.status-value.checking { color: var(--color-warning); }
.status-value.unknown { color: var(--color-ink-muted-48); }
.status-value.mode { color: var(--color-ink); font-weight: 400; }

/* Form Field */
.form-field {
  margin-bottom: var(--space-md);
}

.form-label {
  display: block;
  font: var(--text-caption);
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: var(--space-xxs);
}

/* Apple Input - pill style */
.apple-input {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  color: var(--color-ink);
  font: var(--text-body);
  transition: border-color 0.2s;
  height: 44px;
  box-sizing: border-box;
}

.apple-input:focus {
  outline: none;
  border-color: var(--color-primary);
}

.apple-input.full-width {
  width: 100%;
}

.apple-input::placeholder {
  color: var(--color-ink-muted-48);
}

/* Select - Apple Pill Style (DESIGN.md) */
.select-wrapper {
  position: relative;
}

.apple-select {
  appearance: none;
  padding: var(--spacing-sm) 40px var(--spacing-sm) var(--spacing-md);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  color: var(--color-ink);
  font: var(--text-body);
  height: 44px;
  cursor: pointer;
  transition: border-color 0.2s;
  width: 100%;
  box-sizing: border-box;
}

.apple-select:focus {
  outline: none;
  outline: 2px solid var(--color-primary-focus);
  border-color: transparent;
}

.select-arrow {
  position: absolute;
  right: var(--space-md);
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-ink-muted-48);
  font-size: 18px;
  pointer-events: none;
}

/* Button Icon */
.btn-icon {
  font-size: 14px;
  line-height: 1;
}

/* Search */
.search-wrapper {
  display: flex;
  gap: var(--space-sm);
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
  color: var(--color-ink-muted-48);
  pointer-events: none;
}

.search-input {
  padding: var(--spacing-sm) var(--spacing-md) var(--spacing-sm) 44px;
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  color: var(--color-ink);
  font: var(--text-body);
  transition: border-color 0.2s;
  height: 44px;
  box-sizing: border-box;
  width: 100%;
}

.search-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-hover);
}

.search-input::placeholder {
  color: var(--color-ink-muted-48);
}

/* Search Results */
.search-results {
  margin-top: var(--space-lg);
  border-top: 1px solid var(--color-divider-soft);
  padding-top: var(--space-lg);
}

.search-result-item {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-md) 0;
  border-bottom: 1px solid var(--color-divider-soft);
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
  background: var(--color-surface-pearl);
  border-radius: var(--radius-md);
}

.result-content {
  flex: 1;
  min-width: 0;
}

.result-title {
  font: var(--text-body-strong);
  font-weight: 600;
  color: var(--color-primary);
  margin-bottom: var(--space-xxs);
}

.result-snippet {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
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
  padding: var(--space-xxl);
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: var(--space-md);
  opacity: 0.5;
}

.empty-text {
  font: var(--text-body);
  color: var(--color-ink-muted-48);
  margin: 0;
}
</style>
