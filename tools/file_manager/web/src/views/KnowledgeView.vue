<template>
  <div class="knowledge-view">
    <!-- Header -->
    <header class="knowledge-view__header">
      <h2 class="knowledge-view__title">
        <ColorIcon name="brain" size="lg" />
        <span>知识库</span>
      </h2>
      <div class="knowledge-view__actions">
        <button
          v-if="canSyncKnowledge"
          class="btn-apple-secondary"
          @click="showSyncSettings"
        >
          <ColorIcon name="settings" size="sm" class="knowledge-view__btn-icon" />
          同步设置
        </button>
        <button class="btn-apple-secondary" @click="openLlmWiki">
          <ColorIcon name="book-open" size="sm" class="knowledge-view__btn-icon" />
          打开知识库
        </button>
        <button class="btn-apple-primary" @click="checkLlmWikiStatus">
          <ColorIcon name="refresh" size="sm" class="knowledge-view__btn-icon" />
          检查状态
        </button>
      </div>
    </header>

    <!-- Content -->
    <main class="knowledge-view__content">
      <!-- Sync Status Section -->
      <section class="knowledge-view__section">
        <h3 class="knowledge-view__subsection-title">同步状态</h3>
        <div class="card-utility">
          <div class="knowledge-view__status-grid">
            <div class="knowledge-view__status-item">
              <span class="knowledge-view__status-label">llm_wiki 服务</span>
              <div class="knowledge-view__status-value-wrapper">
                <span class="knowledge-view__status-dot" :class="serviceStatusClass"></span>
                <span class="knowledge-view__status-value" :class="serviceStatusClass">{{ serviceStatus }}</span>
              </div>
            </div>
            <div class="knowledge-view__status-item">
              <span class="knowledge-view__status-label">当前模式</span>
              <span class="knowledge-view__status-value knowledge-view__status-value--mode">{{ syncMode }}</span>
            </div>
          </div>

          <!-- Sync History -->
          <div v-if="syncHistory.length > 0" class="knowledge-view__history">
            <h4 class="knowledge-view__history-title">最近同步</h4>
            <div class="knowledge-view__history-list">
              <div
                v-for="job in syncHistory"
                :key="job.id"
                class="knowledge-view__history-item"
              >
                <span class="knowledge-view__history-status" :class="`knowledge-view__history-status--${job.status}`">
                  {{ jobStatusText(job.status) }}
                </span>
                <span class="knowledge-view__history-path" :title="job.source_path">{{ job.source_path }}</span>
                <span class="knowledge-view__history-time">{{ formatTime(job.completed_at || job.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Sync to Knowledge Base Section -->
      <section v-if="canSyncKnowledge" class="knowledge-view__section">
        <h3 class="knowledge-view__subsection-title">同步到知识库</h3>
        <div class="card-utility">
          <p class="knowledge-view__desc">将 file_manager 中的文档同步到 llm_wiki 知识库进行加工处理。</p>

          <div class="knowledge-view__form-field">
            <label class="knowledge-view__label">选择文件或文件夹</label>
            <div class="knowledge-view__path-input-row">
              <input
                type="text"
                v-model="syncSourcePath"
                placeholder="/path/to/sync"
                class="apple-input knowledge-view__input"
              >
              <button class="btn-apple-secondary" @click="pathPickerVisible = true">
                浏览...
              </button>
            </div>
          </div>

          <div class="knowledge-view__form-field">
            <label class="knowledge-view__label">目标项目</label>
            <div class="knowledge-view__select-wrapper">
              <select v-model="syncProject" class="apple-select knowledge-view__select">
                <option value="default">default</option>
              </select>
              <span class="knowledge-view__select-arrow">›</span>
            </div>
          </div>

          <button class="btn-apple-primary" @click="syncToLlmWiki" :disabled="syncInProgress">
            <ColorIcon :name="syncInProgress ? 'loader' : 'upload'" size="sm" class="knowledge-view__btn-icon" :class="{ 'knowledge-view__btn-icon--spinning': syncInProgress }" />
            {{ syncInProgress ? '同步中...' : '同步到知识库' }}
          </button>

          <!-- Sync Result Feedback -->
          <div v-if="syncResult" class="knowledge-view__sync-result" :class="`knowledge-view__sync-result--${syncResult.type}`">
            <ColorIcon :name="syncResult.type === 'success' ? 'check-circle' : 'alert-circle'" size="sm" />
            <span>{{ syncResult.message }}</span>
            <button
              v-if="syncResult.type === 'error'"
              class="knowledge-view__sync-retry"
              @click="syncToLlmWiki"
            >
              重试
            </button>
          </div>
        </div>
      </section>

      <!-- Search Knowledge Base Section -->
      <section class="knowledge-view__section">
        <h3 class="knowledge-view__subsection-title">搜索知识库</h3>
        <div class="card-utility">
          <div class="knowledge-view__search-wrapper">
            <div class="search-input-wrapper">
              <ColorIcon name="search" size="md" class="search-icon" />
              <input
                type="text"
                v-model="searchQuery"
                @keyup.enter="searchKnowledge"
                @input="onSearchInput"
                placeholder="输入搜索关键词..."
                class="search-input knowledge-view__search-input"
                list="search-suggestions"
              >
              <datalist id="search-suggestions">
                <option v-for="s in searchSuggestions" :key="s" :value="s" />
              </datalist>
            </div>
            <div class="knowledge-view__select-wrapper knowledge-view__select-wrapper--sort">
              <select v-model="searchSort" class="apple-select knowledge-view__select knowledge-view__select--sort">
                <option value="relevance">相关度</option>
                <option value="time">时间</option>
              </select>
              <span class="knowledge-view__select-arrow">›</span>
            </div>
            <div class="knowledge-view__select-wrapper knowledge-view__select-wrapper--type">
              <select v-model="searchFileType" class="apple-select knowledge-view__select knowledge-view__select--type">
                <option value="">全部类型</option>
                <option value="md">Markdown</option>
                <option value="txt">文本</option>
                <option value="pdf">PDF</option>
                <option value="doc">Word</option>
              </select>
              <span class="knowledge-view__select-arrow">›</span>
            </div>
            <button class="btn-apple-secondary" @click="searchKnowledge">搜索</button>
          </div>

          <!-- Search History -->
          <div v-if="searchHistory.length > 0 && !searched" class="knowledge-view__search-history">
            <span class="knowledge-view__search-history-label">最近搜索:</span>
            <button
              v-for="term in searchHistory"
              :key="term"
              class="knowledge-view__search-history-item"
              @click="useSearchHistory(term)"
            >
              {{ term }}
            </button>
          </div>

          <div v-if="searchResults.length > 0" class="knowledge-view__results">
            <div
              v-for="result in searchResults"
              :key="result.id"
              class="knowledge-view__result-item"
              @click="openInLlMWiki(result.path)"
            >
              <ColorIcon name="file" size="lg" class="knowledge-view__result-icon" />
              <div class="knowledge-view__result-content">
                <div class="knowledge-view__result-title" v-html="highlightMatch(result.title, searchQuery)"></div>
                <div class="knowledge-view__result-snippet" v-html="highlightMatch(result.snippet, searchQuery)"></div>
                <div class="knowledge-view__result-meta">
                  <span class="knowledge-view__result-score">匹配度: {{ Math.round(result.score * 100) }}%</span>
                  <span class="knowledge-view__result-path" :title="result.path">{{ result.path }}</span>
                </div>
              </div>
              <div class="knowledge-view__result-actions">
                <button class="btn-apple-secondary btn-sm" @click.stop="openInLlMWiki(result.path)" title="在知识库中打开">
                  <ColorIcon name="external-link" size="sm" />
                </button>
                <button class="btn-apple-secondary btn-sm" @click.stop="copyLink(result.path)" title="复制链接">
                  <ColorIcon name="copy" size="sm" />
                </button>
              </div>
            </div>
          </div>

          <div v-else-if="searched && searchResults.length === 0" class="knowledge-view__empty">
            <ColorIcon name="search" size="xl" class="knowledge-view__empty-icon" />
            <p class="knowledge-view__empty-text">未找到匹配结果</p>
          </div>
        </div>
      </section>

      <!-- Path Picker Modal -->
      <PathPicker
        v-model="pathPickerVisible"
        :initial-path="syncSourcePath || '/'"
        @select="onPathSelected"
      />
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../services/api.js'
import { useAuthStore } from '../stores/authStore'
import { isEditor } from '../utils/permissions'
import { ColorIcon } from '../components/common'
import { useToast } from '../composables/useToast'
import PathPicker from '../components/common/PathPicker.vue'

const authStore = useAuthStore()
const { success, error: showError } = useToast()

// 编辑者+ 权限才能同步文件到知识库
const canSyncKnowledge = computed(() => isEditor(authStore.userRole))

const serviceStatus = ref('检查中...')
const syncMode = ref('-')
const syncInterval = ref(30)
const syncSourcePath = ref('')
const syncProject = ref('default')
const searchQuery = ref('')
const searchResults = ref([])
const searched = ref(false)
const llmWikiGuiUrl = ref('http://127.0.0.1:19827') // 默认值，从API获取
const pathPickerVisible = ref(false)
const syncInProgress = ref(false)

// Sync history from API
const syncHistory = ref([])
const syncResult = ref(null)

// Search features
const searchSort = ref('relevance')
const searchHistory = ref([])
const searchFileType = ref('')
const searchSuggestions = ref([])

const SEARCH_HISTORY_KEY = 'knowledge_search_history'
const MAX_SEARCH_HISTORY = 10

onMounted(async () => {
  await checkLlmWikiStatus()
  await loadSettings()
  loadSyncHistory()
  loadSearchHistory()
})

async function checkLlmWikiStatus() {
  serviceStatus.value = '检查中...'
  try {
    const data = await api.getKnowledgeStatus()
    serviceStatus.value = data.running ? '运行中' : '已停止'
    syncMode.value = data.sync_mode || '手动'
    if (data.llm_wiki_gui_url) {
      llmWikiGuiUrl.value = data.llm_wiki_gui_url
    }
  } catch (err) {
    serviceStatus.value = '未知'
    showError(err.message)
  }
}

async function loadSyncHistory() {
  try {
    const data = await api.getSyncHistory(syncProject.value)
    syncHistory.value = data.jobs || []
  } catch (err) {
    console.warn('Failed to load sync history:', err)
  }
}

async function loadSettings() {
  try {
    const settings = await api.getKnowledgeSettings()
    if (settings.sync_mode) {
      syncMode.value = settings.sync_mode === 'manual' ? '手动' :
                       settings.sync_mode === 'interval' ? '定时同步' : 'Webhook'
    }
    if (settings.sync_interval) {
      syncInterval.value = settings.sync_interval
    }
  } catch (err) {
    console.warn('Failed to load settings:', err)
  }
}

async function showSyncSettings() {
  const mode = prompt('选择同步模式:\n1. manual - 手动\n2. interval - 定时同步\n3. webhook - Webhook', 'manual')
  if (!mode) return

  const modes = { '1': 'manual', '2': 'interval', '3': 'webhook' }
  const selectedMode = modes[mode] || mode

  try {
    const updates = { sync_mode: selectedMode }
    if (selectedMode === 'interval') {
      const interval = prompt('同步间隔（分钟）:', '30')
      if (!interval) return
      updates.sync_interval = parseInt(interval, 10)
    }
    await api.updateKnowledgeSettings(updates)
    syncMode.value = selectedMode
    const modeNames = { 'manual': '手动', 'interval': '定时同步', 'webhook': 'Webhook' }
    success(`同步模式已设置为 ${modeNames[selectedMode] || selectedMode}`)
  } catch (err) {
    showError(err.message)
  }
}

async function openLlmWiki() {
  console.log('[KnowledgeView] openLlmWiki called')

  try {
    // 调用 Tauri 命令 open_llm_wiki（托盘也在用的后端命令）
    // 注意：Tauri v2 使用 window.__TAURI__.invoke，不是自定义的 __TAURI_INVOKE__
    if (window.__TAURI__ && window.__TAURI__.invoke) {
      console.log('[KnowledgeView] Using window.__TAURI__.invoke')
      await window.__TAURI__.invoke('open_llm_wiki')
      console.log('[KnowledgeView] Tauri command completed')
    } else {
      // 非 Tauri 环境（Web）：使用 API
      console.log('[KnowledgeView] Using Web API')
      const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1'
      const resp = await fetch(`${API_BASE}/knowledge/open`)
      const data = await resp.json()
      if (data.error) {
        showError(data.error)
        return
      }
      const url = data.url.replace('http://127.0.0.1', 'http://localhost')
      window.open(url, '_blank')
    }
  } catch (e) {
    console.error('[KnowledgeView] Failed to open knowledge base:', e)
    showError('打开知识库失败: ' + e.message)
  }
}

async function syncToLlmWiki() {
  if (!syncSourcePath.value) {
    showError('请输入同步路径')
    return
  }

  syncInProgress.value = true
  syncResult.value = null
  try {
    const result = await api.syncToKnowledge(syncSourcePath.value, syncProject.value)
    if (result.status === 'completed') {
      const ms = result.duration_ms
      const seconds = ms ? (ms / 1000).toFixed(1) : null
      const filesText = result.files_synced > 0 ? `同步了 ${result.files_synced} 个文件${result.files_failed > 0 ? `，${result.files_failed} 个失败` : ''}` : ''
      const timeText = seconds ? `，耗时 ${seconds} 秒` : ''
      syncResult.value = {
        type: 'success',
        message: `同步完成${filesText}${timeText}`
      }
    } else if (result.status === 'failed') {
      syncResult.value = {
        type: 'error',
        message: result.error_message || '同步失败'
      }
    } else {
      syncResult.value = {
        type: 'success',
        message: '同步已启动'
      }
    }
    // Refresh sync history after sync starts
    setTimeout(loadSyncHistory, 1000)
  } catch (err) {
    syncResult.value = {
      type: 'error',
      message: err.message || '同步失败'
    }
    showError(err.message)
  } finally {
    syncInProgress.value = false
  }
}

async function searchKnowledge() {
  if (!searchQuery.value) {
    showError('请输入搜索关键词')
    return
  }

  // Save to search history
  saveSearchHistory(searchQuery.value)
  searched.value = true
  try {
    const data = await api.searchKnowledge(searchQuery.value, syncProject.value, searchSort.value, searchFileType.value)
    searchResults.value = data.results || []
  } catch (err) {
    showError(err.message)
  }
}

function useSearchHistory(term) {
  searchQuery.value = term
  searchKnowledge()
}

let searchSuggestTimer = null
function onSearchInput() {
  clearTimeout(searchSuggestTimer)
  if (searchQuery.value.length < 2) {
    searchSuggestions.value = []
    return
  }
  searchSuggestTimer = setTimeout(async () => {
    try {
      const data = await api.getSearchSuggestions(searchQuery.value, syncProject.value)
      searchSuggestions.value = data.suggestions || []
    } catch {
      searchSuggestions.value = []
    }
  }, 300)
}

function saveSearchHistory(term) {
  if (!term) return
  let history = JSON.parse(localStorage.getItem(SEARCH_HISTORY_KEY) || '[]')
  history = history.filter(t => t !== term)
  history.unshift(term)
  history = history.slice(0, MAX_SEARCH_HISTORY)
  localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(history))
  loadSearchHistory()
}

function loadSearchHistory() {
  try {
    searchHistory.value = JSON.parse(localStorage.getItem(SEARCH_HISTORY_KEY) || '[]')
  } catch {
    searchHistory.value = []
  }
}

function openInLlMWiki(path) {
  const url = `${llmWikiGuiUrl.value}/doc?path=${encodeURIComponent(path)}`
  if (window.__TAURI_INVOKE__) {
    window.__TAURI_INVOKE__('open_url', { url })
  } else {
    window.open(url, '_blank')
  }
}

function copyLink(path) {
  const url = `${llmWikiGuiUrl.value}/doc?path=${encodeURIComponent(path)}`
  navigator.clipboard.writeText(url).then(() => {
    success('链接已复制到剪贴板')
  }).catch(() => {
    showError('复制失败')
  })
}

function onPathSelected(path) {
  syncSourcePath.value = path
}

function jobStatusText(status) {
  const map = {
    'pending': '等待中',
    'running': '进行中',
    'completed': '已完成',
    'failed': '失败'
  }
  return map[status] || status
}

function formatTime(isoString) {
  if (!isoString) return '-'
  const date = new Date(isoString)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

function highlightMatch(text, query) {
  if (!query || !text) return text
  const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
  return text.replace(regex, '<mark class="knowledge-view__highlight">$1</mark>')
}

const serviceStatusClass = computed(() => ({
  'knowledge-view__status-dot--running': serviceStatus.value === '运行中',
  'knowledge-view__status-dot--stopped': serviceStatus.value === '已停止',
  'knowledge-view__status-dot--checking': serviceStatus.value === '检查中...',
  'knowledge-view__status-dot--unknown': serviceStatus.value === '未知'
}))
</script>

<style scoped>
/* === Block: knowledge-view === */
.knowledge-view {
  /* Layout */
  display: flex;
  flex-direction: column;
  flex: 1;
  height: 100%;
  overflow: auto;
  padding: var(--spacing-lg);
  box-sizing: border-box;

  /* Visual */
  background: transparent;
}

/* === Element: knowledge-view__header === */
.knowledge-view__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--spacing-sm);

  /* Box Model */
  padding: var(--spacing-md) var(--spacing-lg);
  margin-bottom: var(--spacing-md);

  /* Visual - White card like FileView */
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);

  /* Constraint */
  width: 100%;
  max-width: var(--content-max-width-universal);
  margin-left: auto;
  margin-right: auto;
  box-sizing: border-box;
}

/* === Element: knowledge-view__title === */
.knowledge-view__title {
  font: var(--text-tagline);
  color: var(--color-ink);
  margin: 0;
}

/* === Element: knowledge-view__actions === */
.knowledge-view__actions {
  display: flex;
  gap: var(--spacing-sm);
}

/* === Element: knowledge-view__btn-icon === */
.knowledge-view__btn-icon {
  /* Layout */
  flex-shrink: 0;
}

/* === Element: knowledge-view__content === */
.knowledge-view__content {
  width: 100%;
  max-width: var(--content-max-width-universal);
  margin: 0 auto;
  box-sizing: border-box;

  /* Visual - White card like FileView */
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

/* === Element: knowledge-view__section === */
.knowledge-view__section {
  margin-bottom: var(--spacing-xl);
}

/* === Element: knowledge-view__section:last-child === */
.knowledge-view__section:last-child {
  margin-bottom: 0;
}

/* === Element: knowledge-view__card === */
.knowledge-view__card {
  /* Visual - White card */
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);

  /* Box Model */
  margin-bottom: var(--spacing-md);
}

/* === Element: knowledge-view__subsection-title === */
.knowledge-view__subsection-title {
  font: var(--text-body-strong);
  color: var(--color-ink);
  margin: 0 0 var(--spacing-md);
}

/* === Element: knowledge-view__status-grid === */
.knowledge-view__status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-md);
}

/* === Element: knowledge-view__status-item === */
.knowledge-view__status-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xxs);
}

/* === Element: knowledge-view__status-label === */
.knowledge-view__status-label {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

/* === Element: knowledge-view__status-value-wrapper === */
.knowledge-view__status-value-wrapper {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

/* === Element: knowledge-view__status-dot === */
.knowledge-view__status-dot {
  width: var(--spacing-xs);
  height: var(--spacing-xs);
  border-radius: var(--radius-full);
}

.knowledge-view__status-dot--running {
  background: var(--color-success);
}

.knowledge-view__status-dot--stopped {
  background: var(--color-danger);
}

.knowledge-view__status-dot--checking,
.knowledge-view__status-dot--unknown {
  background: var(--color-ink-muted-48);
}

/* === Element: knowledge-view__status-value === */
.knowledge-view__status-value {
  font: var(--text-body-strong);
  color: var(--color-ink);
}

.knowledge-view__status-value--mode {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

/* === Element: knowledge-view__desc === */
.knowledge-view__desc {
  font: var(--text-body);
  color: var(--color-ink-muted-48);
  margin: 0 0 var(--spacing-md);
}

/* === Element: knowledge-view__form-field === */
.knowledge-view__form-field {
  margin-bottom: var(--spacing-md);
}

/* === Element: knowledge-view__label === */
.knowledge-view__label {
  display: block;
  font: var(--text-caption-strong);
  color: var(--color-ink);
  margin-bottom: var(--spacing-xxs);
}

/* === Element: knowledge-view__input === */
.knowledge-view__input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  height: 44px;
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  font: var(--text-body);
  color: var(--color-ink);
  box-sizing: border-box;
  transition: border-color var(--transition-fast);
}

/* === Element: knowledge-view__path-input-row === */
.knowledge-view__path-input-row {
  display: flex;
  gap: var(--spacing-sm);
}

.knowledge-view__path-input-row .knowledge-view__input {
  flex: 1;
}

.knowledge-view__input:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
  border-color: transparent;
}

/* === Element: knowledge-view__select-wrapper === */
.knowledge-view__select-wrapper {
  position: relative;
  display: inline-block;
  width: 100%;
}

/* === Element: knowledge-view__select === */
.knowledge-view__select {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  height: 44px;
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  font: var(--text-body);
  color: var(--color-ink);
  appearance: none;
  cursor: pointer;
  box-sizing: border-box;
}

.knowledge-view__select:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
  border-color: transparent;
}

/* === Element: knowledge-view__select-arrow === */
.knowledge-view__select-arrow {
  position: absolute;
  right: var(--spacing-md);
  top: 50%;
  transform: translateY(-50%);
  font-size: 20px;
  color: var(--color-ink-muted-48);
  pointer-events: none;
}

/* === Element: knowledge-view__search-wrapper === */
.knowledge-view__search-wrapper {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
  margin-bottom: var(--spacing-md);
}

/* === Element: knowledge-view__search-input === */
.knowledge-view__search-input {
  flex: 1;
  padding: var(--spacing-sm) var(--spacing-md);
  height: 44px;
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  font: var(--text-body);
  color: var(--color-ink);
  box-sizing: border-box;
}

.knowledge-view__search-input:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
  border-color: transparent;
}

/* === Element: knowledge-view__results === */
.knowledge-view__results {
  margin-top: var(--spacing-md);
}

/* === Element: knowledge-view__result-item === */
.knowledge-view__result-item {
  display: flex;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-sm);
}

/* === Element: knowledge-view__result-icon === */
.knowledge-view__result-icon {
  /* Layout */
  flex-shrink: 0;
}

/* === Element: knowledge-view__result-content === */
.knowledge-view__result-content {
  flex: 1;
  min-width: 0;
}

/* === Element: knowledge-view__result-title === */
.knowledge-view__result-title {
  font: var(--text-body-strong);
  color: var(--color-ink);
  margin-bottom: var(--spacing-xxs);
}

/* === Element: knowledge-view__result-snippet === */
.knowledge-view__result-snippet {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* === Element: knowledge-view__result-item hover === */
.knowledge-view__result-item:hover {
  border-color: var(--color-primary);
  background: var(--color-canvas-parchment);
  cursor: pointer;
}

/* === Element: knowledge-view__result-meta === */
.knowledge-view__result-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-top: var(--spacing-xs);
}

.knowledge-view__result-score {
  font: var(--text-caption);
  color: var(--color-success);
}

.knowledge-view__result-path {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

/* === Element: knowledge-view__result-actions === */
.knowledge-view__result-actions {
  display: flex;
  gap: var(--spacing-xs);
  align-items: flex-start;
  flex-shrink: 0;
}

.knowledge-view__result-actions .btn-sm {
  padding: var(--spacing-xs);
  min-width: 32px;
}

/* === Element: knowledge-view__empty === */
.knowledge-view__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xxl);
  text-align: center;
}

/* === Element: knowledge-view__empty-icon === */
.knowledge-view__empty-icon {
  /* Box Model */
  margin-bottom: var(--spacing-md);

  /* Visual */
  opacity: 0.5;
}

/* === Element: knowledge-view__empty-text === */
.knowledge-view__empty-text {
  font: var(--text-body);
  color: var(--color-ink-muted-48);
  margin: 0;
}

/* === Element: knowledge-view__btn-icon--spinning === */
.knowledge-view__btn-icon--spinning {
  animation: knowledge-view__spin 1s linear infinite;
}

@keyframes knowledge-view__spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* === Element: knowledge-view__history === */
.knowledge-view__history {
  margin-top: var(--spacing-lg);
  padding-top: var(--spacing-lg);
  border-top: 1px solid var(--color-hairline);
}

/* === Element: knowledge-view__history-title === */
.knowledge-view__history-title {
  font: var(--text-caption-strong);
  color: var(--color-ink-muted-48);
  margin: 0 0 var(--spacing-sm);
}

/* === Element: knowledge-view__history-list === */
.knowledge-view__history-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

/* === Element: knowledge-view__history-item === */
.knowledge-view__history-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font: var(--text-caption);
  color: var(--color-ink);
  padding: var(--spacing-xs) 0;
}

/* === Element: knowledge-view__history-status === */
.knowledge-view__history-status {
  font: var(--text-caption);
  padding: 2px var(--spacing-xs);
  border-radius: var(--radius-sm);
  min-width: 50px;
  text-align: center;
}

.knowledge-view__history-status--pending,
.knowledge-view__history-status--running {
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.knowledge-view__history-status--completed {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.knowledge-view__history-status--failed {
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

/* === Element: knowledge-view__history-path === */
.knowledge-view__history-path {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--color-ink-muted-48);
}

/* === Element: knowledge-view__history-time === */
.knowledge-view__history-time {
  color: var(--color-ink-muted-48);
  flex-shrink: 0;
}

/* === Element: knowledge-view__sync-result === */
.knowledge-view__sync-result {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  font: var(--text-caption);
}

.knowledge-view__sync-result--success {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.knowledge-view__sync-result--error {
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

/* === Element: knowledge-view__sync-retry === */
.knowledge-view__sync-retry {
  margin-left: auto;
  padding: var(--spacing-xxs) var(--spacing-sm);
  background: var(--color-danger);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font: var(--text-caption);
  cursor: pointer;
  transition: opacity 0.15s ease;
}

.knowledge-view__sync-retry:hover {
  opacity: 0.85;
}

/* === Element: knowledge-view__select-wrapper--sort === */
.knowledge-view__select-wrapper--sort {
  width: auto;
  min-width: 100px;
}

/* === Element: knowledge-view__select--sort === */
.knowledge-view__select--sort {
  width: auto;
  min-width: 100px;
  height: 36px;
}

/* === Element: knowledge-view__search-history === */
.knowledge-view__search-history {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-md);
}

/* === Element: knowledge-view__search-history-label === */
.knowledge-view__search-history-label {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

/* === Element: knowledge-view__search-history-item === */
.knowledge-view__search-history-item {
  font: var(--text-caption);
  color: var(--color-primary);
  background: var(--color-primary-bg);
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-pill);
  padding: var(--spacing-xxs) var(--spacing-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.knowledge-view__search-history-item:hover {
  background: var(--color-primary);
  color: white;
}

/* === Element: knowledge-view__highlight === */
.knowledge-view__highlight {
  background: var(--color-warning-bg);
  color: var(--color-ink);
  padding: 0 2px;
  border-radius: 2px;
}
</style>
