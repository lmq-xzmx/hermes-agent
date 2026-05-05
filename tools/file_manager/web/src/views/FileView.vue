<template>
  <div class="file-view">
    <!-- Toolbar -->
    <div class="toolbar" id="fileToolbar">
      <!-- Breadcrumb Navigation -->
      <div class="breadcrumb">
        <button
          v-for="(crumb, index) in breadcrumbs"
          :key="crumb.path"
          class="breadcrumb-item"
          :class="{ active: index === breadcrumbs.length - 1 }"
          @click="navigateToBreadcrumb(crumb)"
        >
          <span v-if="index > 0" class="breadcrumb-separator">/</span>
          {{ crumb.name }}
        </button>
      </div>

      <!-- Path Navigation Buttons -->
      <button class="btn-apple-icon" @click="goBack" :disabled="!canGoBack" title="后退">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M10.5 3.5a.5.5 0 0 0-.5-.5H4.707l2.147-2.146a.5.5 0 1 0-.708-.708l-3 3a.5.5 0 0 0 0 .708l3 3a.5.5 0 0 0 .708-.708L4.707 3.5H10a.5.5 0 0 0 .5-.5z"/></svg>
      </button>
      <button class="btn-apple-icon" @click="goForward" :disabled="!canGoForward" title="前进">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M5.5 3.5a.5.5 0 0 1 .5-.5h6.793l-2.147 2.146a.5.5 0 0 0 .708.708l3-3a.5.5 0 0 0 0-.708l-3-3a.5.5 0 1 1 .708-.708L13.293 3.5H6a.5.5 0 0 1-.5-.5z"/></svg>
      </button>
      <button class="btn-apple-icon" @click="goUp" :disabled="currentPath === '/'" title="上级目录">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M8 4.5a.5.5 0 0 0-.5.5v8a.5.5 0 0 0 .5.5h7a.5.5 0 0 0 .5-.5V6a.5.5 0 0 0-.5-.5h-7a.5.5 0 0 0-.5.5v8a.5.5 0 0 0 .5.5h7a.5.5 0 0 0 .5-.5v-2a.5.5 0 0 0-.5-.5H8a.5.5 0 0 0-.5.5v4z"/></svg>
      </button>

      <div class="toolbar-spacer"></div>
      <!-- Search Box -->
      <SearchInput
        v-model="searchQuery"
        placeholder="搜索文件..."
        @search="onSearchInput"
        @clear="clearSearch"
      />
      <button class="btn-apple-secondary" @click="refresh">刷新</button>
      <button class="btn-apple-secondary" @click="triggerUpload">上传</button>
      <button class="btn-apple-secondary" @click="shareSelected">分享</button>
      <button class="btn-apple-secondary" @click="pasteFiles" :disabled="!canPaste">粘贴</button>
      <div class="view-toggle">
        <button class="view-toggle-btn" :class="{ active: viewMode === 'list' }" @click="setViewMode('list')">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><rect x="2" y="3" width="12" height="2" rx="1"/><rect x="2" y="7" width="12" height="2" rx="1"/><rect x="2" y="11" width="12" height="2" rx="1"/></svg>
        </button>
        <button class="view-toggle-btn" :class="{ active: viewMode === 'grid' }" @click="setViewMode('grid')">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><rect x="2" y="2" width="5" height="5" rx="1"/><rect x="9" y="2" width="5" height="5" rx="1"/><rect x="2" y="9" width="5" height="5" rx="1"/><rect x="9" y="9" width="5" height="5" rx="1"/></svg>
        </button>
      </div>
      <button class="btn-apple-secondary" @click="toggleFloatingWindow" title="打开浮窗">浮窗</button>
    </div>

    <!-- Hidden file input -->
    <input type="file" ref="fileInput" multiple style="display:none" @change="handleFileUpload">

    <!-- Empty State with Guidance -->
    <div class="empty-state" :class="{ show: showEmptyGuidance }">
      <div v-if="searchQuery && filteredFiles.length === 0 && files.length > 0" class="search-no-results">
        <p>未找到包含「{{ searchQuery }}」的文件</p>
      </div>
      <!-- No Spaces: User has no workspaces -->
      <template v-if="emptyGuidanceType === 'no-spaces'">
        <div class="empty-state-guidance">
          <div class="guidance-icon">📁</div>
          <h3>暂无工作空间</h3>
          <p class="guidance-desc">您还没有分配任何工作空间，请联系管理员或创建新空间</p>
          <div class="guidance-actions">
            <button v-if="authStore.userRole === 'admin'" class="btn btn-primary" @click="goToSpaces">
              创建工作空间
            </button>
            <button class="btn btn-secondary" @click="goToSpaces">
              查看所有空间
            </button>
          </div>
        </div>
      </template>

      <!-- Select Space: Multiple spaces available but none selected -->
      <template v-else-if="emptyGuidanceType === 'select-space'">
        <div class="empty-state-guidance">
          <div class="guidance-icon">📂</div>
          <h3>请选择工作空间</h3>
          <p class="guidance-desc">您有多个工作空间，请在左侧选择要访问的空间</p>
          <div class="space-list-preview" v-if="spaceStore.spaces.length > 0">
            <button
              v-for="space in spaceStore.spaces.slice(0, 4)"
              :key="space.space_id"
              class="btn btn-secondary space-quick-select"
              @click="selectSpace(space)"
            >
              {{ space.name || space.space_id }}
            </button>
          </div>
          <button class="btn btn-link" @click="goToSpaces">查看全部 {{ spaceStore.spaces.length }} 个空间</button>
        </div>
      </template>

      <!-- Empty Folder: Space selected but folder is empty -->
      <template v-else>
        <div class="empty-state-icon">📁</div>
        <p>{{ emptyMessage }}</p>
        <p class="empty-hint">点击上方「+ 新建文件夹」或「上传」开始</p>
      </template>
    </div>

    <!-- List View -->
    <div class="file-list-container" :class="{ 'list-view': viewMode === 'list', 'grid-view': viewMode === 'grid' }" v-show="viewMode === 'list'" ref="listContainerRef" @mousedown="startSelection">
      <table class="file-list" v-if="filteredFiles.length > 0">
        <thead>
          <tr>
            <th style="width:40%">
              <label class="checkbox-label">
                <input type="checkbox" class="apple-checkbox" @change="toggleSelectAll" :checked="isAllSelected">
                <span>名称</span>
              </label>
            </th>
            <th style="width:15%">大小</th>
            <th style="width:20%">修改时间</th>
            <th style="width:20%">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="file in filteredFiles" :key="file.path" class="file-row"
              :class="{ selected: selectedFiles.has(file.path) }"
              :data-path="file.path"
              draggable="true"
              @dragstart="onDragStart($event, file)"
              @dragover="onDragOver($event, file)"
              @dragleave="onDragLeave($event)"
              @drop="onDrop($event, file)"
              @click="onRowClick(file, $event)"
              @contextmenu.prevent="onContextMenu($event, file)">
            <td>
              <label class="checkbox-label" @click.stop>
                <input type="checkbox" class="apple-checkbox" :checked="selectedFiles.has(file.path)" @change="toggleFileSelection(file.path)">
                <span class="file-icon-text">{{ file.is_directory ? '📁' : getFileIcon(file.name) }}</span>
                <span class="file-name-text">{{ file.name }}</span>
              </label>
            </td>
            <td class="file-size">{{ file.is_directory ? '-' : formatSize(file.size) }}</td>
            <td>{{ formatDate(file.modified) }}</td>
            <td>
              <div class="file-actions">
                <button @click.stop="openInFinder(file.path)">Finder 中显示</button>
                <button class="danger" @click.stop="deleteItem(file.path, file.is_directory ? 'directory' : 'file')">删除</button>
                <button @click.stop="shareItem(file.path)">分享</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Grid View -->
    <div class="file-grid-container" :class="{ active: viewMode === 'grid' }" v-show="viewMode === 'grid'">
      <div class="file-grid">
        <div v-for="file in filteredFiles" :key="file.path"
             class="file-grid-item"
             :class="{ selected: selectedFiles.has(file.path) }"
             :data-path="file.path"
             draggable="true"
             @click="onGridItemClick(file, $event)"
             @contextmenu.prevent="onContextMenu($event, file)"
             @dragstart="onDragStart($event, file)"
             @dragover="onDragOver($event, file)"
             @dragleave="onDragLeave($event)"
             @drop="onDrop($event, file)">
          <div class="file-icon-grid">{{ file.is_directory ? '📁' : getFileIcon(file.name) }}</div>
          <div class="file-name" :title="file.name">{{ file.name }}</div>
        </div>
      </div>
      <div class="empty-state" :class="{ show: filteredFiles.length === 0 && !searchQuery }" v-show="viewMode === 'grid'">
        <div class="empty-state-icon">📁</div>
        <p>此文件夹为空</p>
      </div>
    </div>

    <!-- Selection Rectangle -->
    <div
      v-if="isSelecting && selectionRect"
      class="selection-rect"
      :style="{
        left: selectionRect.left + 'px',
        top: selectionRect.top + 'px',
        width: selectionRect.width + 'px',
        height: selectionRect.height + 'px'
      }"
    ></div>

    <!-- Multi-Selection Action Bar -->
    <div v-if="selectedFiles.size > 0" class="multi-select-bar">
      <div class="multi-select-info">
        <span class="multi-select-count">已选择 {{ selectedFiles.size }} 项</span>
        <button class="btn-apple-link-sm" @click="clearSelection">取消选择</button>
      </div>
      <div class="multi-select-actions">
        <button class="btn-apple-secondary btn-sm" @click="shareSelected">分享</button>
        <button class="btn-apple-secondary btn-sm" @click="downloadSelected">下载</button>
        <button class="btn-apple-secondary btn-sm" @click="pasteFiles" :disabled="!canPaste">粘贴</button>
        <button class="btn-apple-danger btn-sm" @click="deleteSelected">删除</button>
      </div>
    </div>

    <!-- Context Menu -->
    <FileContextMenu
      ref="contextMenuRef"
      :can-paste="canPaste"
      @open="onContextOpen"
      @open-in-finder="onContextOpenInFinder"
      @rename="onContextRename"
      @copy="onContextCopy"
      @cut="onContextCut"
      @paste="onContextPaste"
      @share="onContextShare"
      @delete="onContextDelete"
    />

    <!-- Preview Modal -->
    <PreviewModal
      :visible="previewVisible"
      :file="previewFile"
      :files="previewableFiles"
      :current-index="previewIndex"
      :content="previewContent"
      :loading="previewLoading"
      :error="previewError"
      @close="closePreview"
      @navigate="onPreviewNavigate"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../services/api.js'
import { useSpaceStore } from '../stores/spaceStore.js'
import { useAuthStore } from '../stores/authStore.js'
import FileContextMenu from '../components/FileContextMenu.vue'
import PreviewModal from '../components/PreviewModal.vue'
import SearchInput from '../components/common/SearchInput.vue'
import { useDragSelection } from '../composables/useDragSelection'
import { useKeyboardShortcuts } from '../composables/useKeyboardShortcuts.js'
import { useGuidanceTrigger } from '../composables/useGuidanceTrigger.js'

const props = defineProps({
  currentPath: { type: String, default: '/' }
})

const emit = defineEmits(['navigate', 'show-preview', 'show-toast'])

// Space store for current space management
const spaceStore = useSpaceStore()
const authStore = useAuthStore()
const router = useRouter()
const { onFirstFileUploaded, onFileUploaded } = useGuidanceTrigger()

// Computed: get currentSpaceId from store
const currentSpaceId = computed(() => spaceStore.currentSpaceId)

const files = ref([])
const selectedFiles = ref(new Set())
const viewMode = ref('list')
const loading = ref(false)
const fileInput = ref(null)
const VIEW_MODES = { LIST: 'list', GRID: 'grid' }
const contextMenuRef = ref(null)
const clipboard = ref({ mode: null, paths: [] })
const listContainerRef = ref(null)
const searchQuery = ref('')

// Preview state
const previewVisible = ref(false)
const previewFile = ref(null)
const previewContent = ref('')
const previewLoading = ref(false)
const previewError = ref('')

// Computed for preview
const previewableFiles = computed(() => filteredFiles.value.filter(f => !f.is_directory))

// Filtered files based on search query
const filteredFiles = computed(() => {
  if (!searchQuery.value.trim()) {
    return files.value
  }
  const query = searchQuery.value.toLowerCase().trim()
  return files.value.filter(f => f.name.toLowerCase().includes(query))
})
const previewIndex = computed(() => {
  if (!previewFile.value) return -1
  return previewableFiles.value.findIndex(f => f.path === previewFile.value.path)
})

// Initialize drag selection
const {
  isSelecting,
  selectionRect,
  startSelection,
  toggleSelection: dragToggle
} = useDragSelection(listContainerRef, {
  onSelectionChange: (paths) => {
    selectedFiles.value = new Set(paths)
  }
})

const emptyMessage = computed(() => {
  if (!spaceStore.hasSpaces) {
    return '您还没有工作空间'
  }
  if (!currentSpaceId.value) {
    return '请先选择一个工作空间'
  }
  return '此文件夹为空'
})

// Empty state guidance
const showEmptyGuidance = computed(() => {
  return files.value.length === 0 && !loading.value
})

const emptyGuidanceType = computed(() => {
  if (!spaceStore.hasSpaces) return 'no-spaces'
  if (!currentSpaceId.value) return 'select-space'
  return 'empty-folder'
})

// Select a space
async function selectSpace(space) {
  await spaceStore.selectSpace(space)
  loadFiles(props.currentPath)
}

// Navigate to spaces page
function goToSpaces() {
  router.push('/spaces')
}

const canPaste = computed(() => clipboard.value.mode && clipboard.value.paths.length > 0)

// Navigation history
const navigationHistory = ref(['/'])
const historyIndex = ref(0)

const canGoBack = computed(() => historyIndex.value > 0)
const canGoForward = computed(() => historyIndex.value < navigationHistory.value.length - 1)

// Breadcrumbs
const breadcrumbs = computed(() => {
  const parts = props.currentPath.split('/').filter(p => p)
  const crumbs = [{ name: '根目录', path: '/' }]
  let currentPath = ''
  for (const part of parts) {
    currentPath += '/' + part
    crumbs.push({ name: part, path: currentPath })
  }
  return crumbs
})

function navigateToBreadcrumb(crumb) {
  if (crumb.path !== props.currentPath) {
    emit('navigate', { path: crumb.path })
  }
}

// Navigation functions
function goBack() {
  if (canGoBack.value) {
    historyIndex.value--
    emit('navigate', { path: navigationHistory.value[historyIndex.value] })
  }
}

function goForward() {
  if (canGoForward.value) {
    historyIndex.value++
    emit('navigate', { path: navigationHistory.value[historyIndex.value] })
  }
}

function goUp() {
  const parentPath = props.currentPath.split('/').slice(0, -1).join('/') || '/'
  emit('navigate', { path: parentPath })
}

function addToHistory(path) {
  // Remove any forward history
  navigationHistory.value = navigationHistory.value.slice(0, historyIndex.value + 1)
  // Add new path
  if (navigationHistory.value[navigationHistory.value.length - 1] !== path) {
    navigationHistory.value.push(path)
    historyIndex.value = navigationHistory.value.length - 1
  }
}

// Watch for path changes to add to history
watch(() => props.currentPath, (newPath) => {
  addToHistory(newPath)
})

// Check if all files are selected
const isAllSelected = computed(() => {
  return filteredFiles.value.length > 0 && filteredFiles.value.every(f => selectedFiles.value.has(f.path))
})

function clearSelection() {
  selectedFiles.value.clear()
}

function downloadSelected() {
  emit('show-toast', { type: 'info', title: '提示', message: '批量下载功能开发中' })
}

async function deleteSelected() {
  if (selectedFiles.value.size === 0) return
  if (!confirm(`确定要删除选中的 ${selectedFiles.value.size} 个项目吗？`)) return

  loading.value = true
  try {
    for (const path of selectedFiles.value) {
      const file = files.value.find(f => f.path === path)
      if (file && file.id) {
        await api.deleteFile(currentSpaceId.value, file.id, props.currentPath)
      }
    }
    emit('show-toast', { type: 'success', title: '已删除', message: `${selectedFiles.value.size} 个项目已删除` })
    selectedFiles.value.clear()
    loadFiles(props.currentPath)
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  } finally {
    loading.value = false
  }
}

// Get first selected file
function getFirstSelectedFile() {
  const selectedPaths = [...selectedFiles.value]
  if (selectedPaths.length === 0) return null
  return files.value.find(f => f.path === selectedPaths[0]) || null
}

// Initialize keyboard shortcuts
const { lastKey } = useKeyboardShortcuts({
  onCopy: () => {
    const file = getFirstSelectedFile()
    if (file) copyFile(file)
  },
  onCut: () => {
    const file = getFirstSelectedFile()
    if (file) cutFile(file)
  },
  onPaste: () => {
    if (canPaste.value) pasteFiles()
  },
  onDelete: () => {
    const file = getFirstSelectedFile()
    if (file) onContextDelete(file)
  },
  onSelectAll: () => {
    const allPaths = filteredFiles.value.map(f => f.path)
    allPaths.forEach(path => selectedFiles.value.add(path))
  },
  onEscape: () => {
    selectedFiles.value.clear()
  },
  onArrowUp: (e) => {
    e.preventDefault()
    navigateSelection(-1)
  },
  onArrowDown: (e) => {
    e.preventDefault()
    navigateSelection(1)
  },
})

// Navigate selection up/down
function navigateSelection(direction) {
  if (filteredFiles.value.length === 0) return

  const paths = [...selectedFiles.value]
  if (paths.length === 0) {
    // Select first file
    selectedFiles.value.add(filteredFiles.value[0].path)
    return
  }

  const currentPath = paths[paths.length - 1]
  const currentIndex = filteredFiles.value.findIndex(f => f.path === currentPath)
  const newIndex = Math.max(0, Math.min(filteredFiles.value.length - 1, currentIndex + direction))

  if (filteredFiles.value[newIndex]) {
    selectedFiles.value.clear()
    selectedFiles.value.add(filteredFiles.value[newIndex].path)
  }
}

// Load files when path or space changes
watch(() => [props.currentPath, currentSpaceId.value], () => {
  if (currentSpaceId.value) {
    loadFiles(props.currentPath)
  }
}, { immediate: true })

// Load spaces on mount
onMounted(async () => {
  if (spaceStore.spaces.length === 0) {
    await spaceStore.loadSpaces()
  }
})

async function loadFiles(path) {
  if (!currentSpaceId.value) return

  loading.value = true
  try {
    const data = await api.getFiles(currentSpaceId.value, path)
    files.value = data.files || []
    emit('navigate', { path })
  } catch (err) {
    emit('show-toast', { type: 'error', title: '加载失败', message: err.message })
  } finally {
    loading.value = false
  }
}

function onRowClick(file, event) {
  if (event.ctrlKey || event.metaKey) {
    toggleFileSelection(file.path)
    return
  }
  if (file.is_directory) {
    emit('navigate', { path: file.path })
  } else {
    openPreview(file)
  }
}

function onGridItemClick(file, event) {
  onRowClick(file, event)
}

function onContextMenu(event, file) {
  event.preventDefault()
  contextMenuRef.value?.show(event, file)
}

function toggleFileSelection(path) {
  if (selectedFiles.value.has(path)) {
    selectedFiles.value.delete(path)
  } else {
    selectedFiles.value.add(path)
  }
}

function toggleSelectAll(checked) {
  if (checked) {
    filteredFiles.value.forEach(f => selectedFiles.value.add(f.path))
  } else {
    selectedFiles.value.clear()
  }
}

function setViewMode(mode) {
  viewMode.value = mode
}

function triggerUpload() {
  fileInput.value?.click()
}

async function handleFileUpload(event) {
  const fileList = event.target.files
  if (!fileList.length) return

  const isFirstUpload = files.value.length === 0 // 上传前文件列表为空则是第一个文件
  const totalCount = files.value.length + fileList.length // 上传后预期总数

  loading.value = true
  try {
    for (const file of fileList) {
      await api.uploadFile(currentSpaceId.value, file, props.currentPath)
    }

    // TC-M3-001: 文件上传触发引导事件
    if (isFirstUpload) {
      // 第一个文件上传成功，触发首次上传引导
      const firstFile = fileList[0]
      const space = spaceStore.currentSpace
      onFirstFileUploaded(
        { id: `temp_${Date.now()}`, name: firstFile.name },
        { id: currentSpaceId.value, ...space }
      )
    } else {
      // 非首次上传，触发累计上传引导
      const lastFile = fileList[fileList.length - 1]
      onFileUploaded(
        { id: `temp_${Date.now()}`, name: lastFile.name },
        { id: currentSpaceId.value },
        totalCount
      )
    }

    emit('show-toast', { type: 'success', title: '上传成功', message: `${fileList.length} 个文件已上传` })
    loadFiles(props.currentPath)
  } catch (err) {
    emit('show-toast', { type: 'error', title: '上传错误', message: err.message })
  } finally {
    loading.value = false
    event.target.value = ''
  }
}

async function deleteItem(path, type) {
  const name = path.split('/').pop()
  if (!confirm(`确定要删除 "${name}" 吗？${type === 'directory' ? '\n这将删除所有内容。' : ''}`)) return

  loading.value = true
  try {
    // Find file by path and get file ID
    const file = files.value.find(f => f.path === path)
    if (file && file.id) {
      await api.deleteFile(currentSpaceId.value, file.id, props.currentPath)
    }
    emit('show-toast', { type: 'success', title: '已删除', message: '删除成功' })
    loadFiles(props.currentPath)
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  } finally {
    loading.value = false
  }
}

async function shareItem(path) {
  const name = path.split('/').pop()
  try {
    const file = files.value.find(f => f.path === path)
    if (file && file.id) {
      const result = await api.shareFile(currentSpaceId.value, file.id)
      emit('show-toast', { type: 'success', title: '已分享', message: result.share_url || '分享链接已生成' })
    }
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

function shareSelected() {
  if (selectedFiles.value.size === 1) {
    shareItem([...selectedFiles.value][0])
  } else if (selectedFiles.value.size > 1) {
    emit('show-toast', { type: 'info', title: '提示', message: '分享功能仅支持单个文件' })
  }
}

function openInFinder(path) {
  if (window.platform?.api?.isTauri) {
    window.platform.api.openPath(path)
      .then(() => emit('show-toast', { type: 'success', title: '已打开', message: '文件已在 Finder 中显示' }))
      .catch(e => emit('show-toast', { type: 'error', title: '错误', message: '无法打开' }))
  } else {
    // Web mode: show path
    const storageRoot = '/Users/xzmx/.hermes/file_manager/storage'
    const absolutePath = storageRoot + '/' + path
    emit('show-toast', { type: 'info', title: '路径', message: absolutePath })
  }
}

function refresh() {
  loadFiles(props.currentPath)
}

function onSearchInput() {
  // Search is reactive via computed property
}

function clearSearch() {
  searchQuery.value = ''
}

// Clipboard functions
function copyFile(file) {
  clipboard.value = { mode: 'copy', paths: [file.path] }
  emit('show-toast', { type: 'success', title: '已复制', message: '文件已复制到剪贴板' })
}

function cutFile(file) {
  clipboard.value = { mode: 'cut', paths: [file.path] }
  emit('show-toast', { type: 'success', title: '已剪切', message: '文件已剪切到剪贴板' })
}

async function pasteFiles() {
  if (!clipboard.value.mode || clipboard.value.paths.length === 0) return

  loading.value = true
  try {
    for (const sourcePath of clipboard.value.paths) {
      const name = sourcePath.split('/').pop()
      const targetPath = props.currentPath === '/' ? `/${name}` : `${props.currentPath}/${name}`
      const file = files.value.find(f => f.path === sourcePath)
      if (file && file.id) {
        await api.moveFile(currentSpaceId.value, file.id, sourcePath, targetPath)
      }
    }
    emit('show-toast', { type: 'success', title: '已粘贴', message: '文件已粘贴到当前位置' })
    if (clipboard.value.mode === 'cut') {
      clipboard.value = { mode: null, paths: [] }
    }
    loadFiles(props.currentPath)
  } catch (err) {
    emit('show-toast', { type: 'error', title: '粘贴失败', message: err.message })
  } finally {
    loading.value = false
  }
}

// Preview functions
async function openPreview(file) {
  previewFile.value = file
  previewVisible.value = true
  previewError.value = ''
  previewContent.value = ''

  if (!file.is_directory) {
    previewLoading.value = true
    try {
      const data = await api.getFileContent(currentSpaceId.value, file.path)
      previewContent.value = data.content || ''
    } catch (err) {
      previewError.value = '无法加载文件内容: ' + err.message
    } finally {
      previewLoading.value = false
    }
  }
}

function closePreview() {
  previewVisible.value = false
  previewFile.value = null
  previewContent.value = ''
  previewError.value = ''
}

function onPreviewNavigate(index) {
  const files = previewableFiles.value
  if (index >= 0 && index < files.length) {
    openPreview(files[index])
  }
}

async function renameFile(file) {
  const oldName = file.name
  const newName = prompt('请输入新名称:', oldName)
  if (!newName || newName === oldName) return

  loading.value = true
  try {
    const sourcePath = file.path
    const targetPath = sourcePath.replace(/\/[^/]+$/, '') + '/' + newName
    if (file.is_directory) {
      // For directories, we'd need a move/rename API
      emit('show-toast', { type: 'info', title: '提示', message: '重命名功能开发中' })
    } else {
      // For files, try to use move
      if (file.id) {
        await api.moveFile(currentSpaceId.value, file.id, sourcePath, targetPath)
        emit('show-toast', { type: 'success', title: '已重命名', message: `"${oldName}" 已重命名为 "${newName}"` })
        loadFiles(props.currentPath)
      }
    }
  } catch (err) {
    emit('show-toast', { type: 'error', title: '重命名失败', message: err.message })
  } finally {
    loading.value = false
  }
}

// Context menu handlers
function onContextOpen(file) {
  if (file.is_directory) {
    emit('navigate', { path: file.path })
  } else {
    openPreview(file)
  }
}

function onContextOpenInFinder(file) {
  openInFinder(file.path)
}

function onContextRename(file) {
  renameFile(file)
}

function onContextCopy(file) {
  copyFile(file)
}

function onContextCut(file) {
  cutFile(file)
}

function onContextPaste(file) {
  pasteFiles()
}

function onContextShare(file) {
  shareItem(file.path)
}

function onContextDelete(file) {
  deleteItem(file.path, file.is_directory ? 'directory' : 'file')
}

async function createFolder() {
  const name = prompt('请输入文件夹名称:')
  if (!name) return

  loading.value = true
  try {
    const targetPath = props.currentPath === '/' ? `/${name}` : `${props.currentPath}/${name}`
    await api.createFolder(currentSpaceId.value, targetPath)
    emit('show-toast', { type: 'success', title: '已创建', message: `文件夹 "${name}" 已创建` })
    loadFiles(props.currentPath)
  } catch (err) {
    emit('show-toast', { type: 'error', title: '创建失败', message: err.message })
  } finally {
    loading.value = false
  }
}

async function createFile() {
  const name = prompt('请输入文件名称:')
  if (!name) return

  loading.value = true
  try {
    const targetPath = props.currentPath === '/' ? `/${name}` : `${props.currentPath}/${name}`
    await api.createFile(currentSpaceId.value, targetPath, '')
    emit('show-toast', { type: 'success', title: '已创建', message: `文件 "${name}" 已创建` })
    loadFiles(props.currentPath)
  } catch (err) {
    emit('show-toast', { type: 'error', title: '创建失败', message: err.message })
  } finally {
    loading.value = false
  }
}

function toggleFloatingWindow() {
  if (window.__TAURI_INVOKE__) {
    window.__TAURI_INVOKE__('show_floating_window')
  }
}

// Get file icon based on file extension
function getFileIcon(filename) {
  const ext = filename.split('.').pop()?.toLowerCase()
  const iconMap = {
    // Images
    'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️', 'bmp': '🖼️', 'svg': '🖼️', 'webp': '🖼️',
    // Videos
    'mp4': '🎬', 'avi': '🎬', 'mov': '🎬', 'wmv': '🎬', 'mkv': '🎬', 'webm': '🎬',
    // Audio
    'mp3': '🎵', 'wav': '🎵', 'flac': '🎵', 'aac': '🎵', 'ogg': '🎵', 'm4a': '🎵',
    // Documents
    'pdf': '📄', 'doc': '📄', 'docx': '📄', 'xls': '📄', 'xlsx': '📄', 'ppt': '📄', 'pptx': '📄',
    // Text
    'txt': '📝', 'md': '📝', 'json': '📝', 'xml': '📝', 'html': '📝', 'css': '📝', 'js': '📝', 'ts': '📝',
    // Archives
    'zip': '📦', 'rar': '📦', '7z': '📦', 'tar': '📦', 'gz': '📦',
    // Default
  }
  return iconMap[ext] || '📄'
}

// Drag and drop
function onDragStart(event, file) {
  event.dataTransfer.setData('application/x-hermes-file', JSON.stringify({
    path: file.path,
    name: file.name,
    type: file.is_directory ? 'directory' : 'file'
  }))
  event.target.style.opacity = '0.5'
}

function onDragOver(event, file) {
  if (file.is_directory) {
    event.preventDefault()
    event.target.classList.add('drag-over')
  }
}

function onDragLeave(event) {
  event.target.classList.remove('drag-over')
}

async function onDrop(event, targetFolder) {
  event.preventDefault()
  event.target.classList.remove('drag-over')

  if (targetFolder.is_directory !== true) return

  const sourceData = event.dataTransfer.getData('application/x-hermes-file')
  if (!sourceData) return

  const { path: sourcePath, name: sourceName } = JSON.parse(sourceData)
  if (sourcePath === targetFolder.path) return

  try {
    const file = files.value.find(f => f.path === sourcePath)
    if (file && file.id) {
      await api.moveFile(currentSpaceId.value, file.id, sourcePath, targetFolder.path + '/' + sourceName)
    }
    emit('show-toast', { type: 'success', title: '已移动', message: `"${sourceName}" 已移动` })
    loadFiles(props.currentPath)
  } catch (err) {
    emit('show-toast', { type: 'error', title: '移动失败', message: err.message })
  }
}

// Utility functions
function formatSize(bytes) {
  if (!bytes) return '-'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let i = 0
  while (bytes >= 1024 && i < units.length - 1) {
    bytes /= 1024
    i++
  }
  return `${bytes.toFixed(1)} ${units[i]}`
}

function formatDate(str) {
  if (!str) return '-'
  const d = new Date(str)
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.file-view {
  flex: 1;
  overflow: auto;
  padding: var(--space-section, 80px);
  background-color: var(--color-canvas-parchment, #f5f5f7);
}

/* Toolbar */
.toolbar {
  display: flex;
  align-items: center;
  gap: var(--space-sm, 12px);
  padding: var(--space-md, 17px) var(--space-lg, 24px);
  background: var(--color-canvas, #ffffff);
  border: 1px solid var(--color-hairline, #e0e0e0);
  border-radius: var(--rounded-lg, 18px);
  margin-bottom: var(--space-md, 17px);
  max-width: 1440px;
  margin-left: auto;
  margin-right: auto;
}

.btn-apple-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background-color: var(--color-primary, #0066cc);
  color: var(--color-on-primary, #ffffff);
  border: none;
  border-radius: var(--rounded-pill, 9999px);
  padding: 10px 20px;
  font: var(--text-body, 17px/1.47 -0.374px);
  cursor: pointer;
  transition: transform 0.1s ease;
  white-space: nowrap;
}

.btn-apple-primary:active {
  transform: scale(0.95);
}

.btn-apple-primary:focus {
  outline: 2px solid var(--color-primary-focus, #0071e3);
  outline-offset: 2px;
}

.btn-apple-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-apple-secondary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background-color: transparent;
  color: var(--color-primary, #0066cc);
  border: 1px solid var(--color-primary, #0066cc);
  border-radius: var(--rounded-pill, 9999px);
  padding: 10px 20px;
  font: var(--text-body, 17px/1.47 -0.374px);
  cursor: pointer;
  transition: transform 0.1s ease;
  white-space: nowrap;
}

.btn-apple-secondary:active {
  transform: scale(0.95);
}

.btn-apple-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.toolbar-spacer {
  flex: 1;
  min-width: var(--space-md, 17px);
}

/* Breadcrumb Navigation */
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 4px;
  font: var(--text-caption, 14px/1.43 -0.224px);
}

.breadcrumb-item {
  background: none;
  border: none;
  color: var(--color-ink-muted-48, #7a7a7a);
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--rounded-sm, 8px);
  display: flex;
  align-items: center;
  gap: 4px;
  transition: background 0.15s;
}

.breadcrumb-item:hover {
  background: var(--color-canvas-parchment, #f5f5f7);
  color: var(--color-ink, #1d1d1f);
}

.breadcrumb-item.active {
  color: var(--color-primary, #0066cc);
  font-weight: 600;
}

.breadcrumb-separator {
  color: var(--color-ink-muted-48, #7a7a7a);
}

/* Apple Icon Button */
.btn-apple-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--color-hairline, #e0e0e0);
  border-radius: var(--rounded-sm, 8px);
  color: var(--color-ink-muted-48, #7a7a7a);
  cursor: pointer;
  transition: background-color 0.15s, color 0.15s;
}
.btn-apple-icon:hover { background-color: var(--color-canvas-parchment, #f5f5f7); color: var(--color-ink, #1d1d1f); }
.btn-apple-icon:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-apple-icon:active { transform: scale(0.95); }

/* View Toggle - Apple Segment Control */
.view-toggle {
  display: flex;
  gap: 0;
  margin-left: var(--space-xs, 8px);
  background: var(--color-canvas-parchment, #f5f5f7);
  border-radius: var(--rounded-sm, 8px);
  padding: 2px;
}

.view-toggle-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--rounded-xs, 5px);
  color: var(--color-ink-muted-48, #7a7a7a);
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.view-toggle-btn:hover {
  color: var(--color-ink, #1d1d1f);
}

.view-toggle-btn.active {
  background-color: var(--color-canvas, #ffffff);
  color: var(--color-ink, #1d1d1f);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* File Grid */
.file-grid-container.active {
  display: block;
}

.file-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: var(--space-lg, 24px);
  padding: var(--space-md, 17px) 0;
}

.file-grid-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-lg, 24px);
  background: var(--color-canvas, #ffffff);
  border: 1px solid var(--color-hairline, #e0e0e0);
  border-radius: var(--rounded-lg, 18px);
  cursor: pointer;
  transition: border-color 0.2s ease, transform 0.1s ease;
}

.file-grid-item:hover {
  border-color: var(--color-primary, #0066cc);
}

.file-grid-item:active {
  transform: scale(0.98);
}

.file-grid-item.selected {
  background: rgba(0, 102, 204, 0.08);
  border-color: var(--color-primary, #0066cc);
  outline: 2px solid var(--color-primary, #0066cc);
  outline-offset: 2px;
}

.file-grid-item .file-icon {
  font-size: 48px;
  margin-bottom: var(--space-sm, 12px);
}

.file-grid-item .file-name {
  font: var(--text-caption, 14px/1.43 -0.224px);
  text-align: center;
  word-break: break-word;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--color-ink, #1d1d1f);
}

/* Empty State */
.empty-state {
  display: none;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px var(--space-lg, 24px);
  color: var(--color-ink-muted-48, #7a7a7a);
}

.empty-state.show {
  display: flex;
}

.empty-state-icon {
  font-size: 64px;
  margin-bottom: var(--space-lg, 24px);
  opacity: 0.5;
}

.empty-hint {
  font: var(--text-caption, 14px/1.43 -0.224px);
  color: var(--color-ink-muted-48, #7a7a7a);
  margin-top: var(--space-sm, 12px);
}

/* Empty State Guidance */
.empty-state-guidance {
  text-align: center;
  padding: var(--space-xl, 32px) var(--space-lg, 24px);
}

.empty-state-guidance .guidance-icon {
  font-size: 80px;
  margin-bottom: var(--space-lg, 24px);
}

.empty-state-guidance h3 {
  font: var(--text-lead, 28px/1.14 0.196px);
  font-weight: 600;
  color: var(--color-ink, #1d1d1f);
  margin: 0 0 var(--space-sm, 12px) 0;
}

.empty-state-guidance .guidance-desc {
  font: var(--text-body, 17px/1.47 -0.374px);
  color: var(--color-ink-muted-48, #7a7a7a);
  margin-bottom: var(--space-xl, 32px);
  max-width: 400px;
}

.empty-state-guidance .guidance-actions {
  display: flex;
  gap: var(--space-sm, 12px);
  justify-content: center;
  flex-wrap: wrap;
}

.empty-state-guidance .space-list-preview {
  display: flex;
  gap: var(--space-xs, 8px);
  justify-content: center;
  flex-wrap: wrap;
  margin-top: var(--space-md, 17px);
}

.empty-state-guidance .space-quick-select {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Search No Results */
.search-no-results {
  padding: var(--space-xl, 32px);
  text-align: center;
  color: var(--color-ink-muted-48, #7a7a7a);
  font: var(--text-body, 17px/1.47 -0.374px);
}

.search-no-results p {
  margin: 0;
}

/* Apple Checkbox */
.apple-checkbox {
  width: 18px;
  height: 18px;
  border-radius: 4px;
  border: 2px solid var(--color-hairline, #e0e0e0);
  background: var(--color-canvas, #ffffff);
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  position: relative;
  vertical-align: middle;
  margin-right: 8px;
  flex-shrink: 0;
}

.apple-checkbox:checked {
  background: var(--color-primary, #0066cc);
  border-color: var(--color-primary, #0066cc);
}

.apple-checkbox:checked::after {
  content: '';
  position: absolute;
  left: 5px;
  top: 2px;
  width: 5px;
  height: 9px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.apple-checkbox:focus {
  outline: 2px solid var(--color-primary-focus, #0071e3);
  outline-offset: 2px;
}

/* File List Container */
.file-list-container {
  width: 100%;
}

.file-list {
  width: 100%;
  border-collapse: collapse;
  background: var(--color-canvas, #ffffff);
  border-radius: var(--rounded-lg, 18px);
  overflow: hidden;
  border: 1px solid var(--color-hairline, #e0e0e0);
}

.file-list th,
.file-list td {
  text-align: left;
  padding: var(--space-sm, 12px) var(--space-md, 17px);
}

.file-list th {
  background: var(--color-canvas-parchment, #f5f5f7);
  font: var(--text-caption-strong, 14px/1.29 -0.224px 600);
  text-transform: uppercase;
  color: var(--color-ink-muted-48, #7a7a7a);
  position: sticky;
  top: 0;
  border-bottom: 1px solid var(--color-hairline, #e0e0e0);
}

.file-list tr:hover td {
  background: var(--color-surface-pearl, #fafafc);
}

/* Selected row highlight */
.file-row.selected td {
  background: rgba(0, 102, 204, 0.08);
}

.file-row.selected td:first-child {
  border-left: 3px solid var(--color-primary, #0066cc);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--space-sm, 12px);
  cursor: pointer;
  height: 44px;
  font: var(--text-body, 17px/1.47 -0.374px);
  color: var(--color-ink, #1d1d1f);
}

.file-icon-text {
  font-size: 20px;
  flex-shrink: 0;
}

.file-name-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-name {
  display: flex;
  align-items: center;
  gap: var(--space-sm, 12px);
  cursor: pointer;
  font: var(--text-body, 17px/1.47 -0.374px);
  color: var(--color-ink, #1d1d1f);
}

.file-name:hover {
  color: var(--color-primary, #0066cc);
}

.file-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.file-size {
  color: var(--color-ink-muted-48, #7a7a7a);
  font: var(--text-caption, 14px/1.43 -0.224px);
}

.file-actions {
  display: flex;
  gap: var(--space-xs, 8px);
  opacity: 0;
  transition: opacity 0.2s;
}

tr:hover .file-actions {
  opacity: 1;
}

.file-actions button {
  background: none;
  border: none;
  color: var(--color-primary, #0066cc);
  cursor: pointer;
  padding: 6px 12px;
  border-radius: var(--rounded-sm, 8px);
  font: var(--text-caption, 14px/1.43 -0.224px);
  transition: background-color 0.15s ease;
}

.file-actions button:hover {
  background: var(--color-surface-pearl, #fafafc);
}

.file-actions button.danger {
  color: #f85149;
}

.file-row.drag-over {
  background: rgba(0, 102, 204, 0.08);
  outline: 2px dashed var(--color-primary, #0066cc);
}

/* Selection Rectangle */
.selection-rect {
  position: fixed;
  border: 2px dashed var(--color-primary, #0066cc);
  background: rgba(0, 102, 204, 0.1);
  pointer-events: none;
  z-index: 9998;
  border-radius: 2px;
}

/* Multi-Selection Action Bar */
.multi-select-bar {
  position: fixed;
  bottom: var(--space-xl, 32px);
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-lg, 24px);
  padding: var(--space-md, 17px) var(--space-lg, 24px);
  background: rgba(245, 245, 247, 0.9);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--color-hairline, #e0e0e0);
  border-radius: var(--rounded-lg, 18px);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  min-width: 400px;
}

.multi-select-info {
  display: flex;
  align-items: center;
  gap: var(--space-md, 17px);
}

.multi-select-count {
  font: var(--text-body-strong, 17px/1.24 -0.374px 600);
  color: var(--color-ink, #1d1d1f);
}

.multi-select-actions {
  display: flex;
  gap: var(--space-xs, 8px);
}

.btn-apple-link-sm {
  background: none;
  border: none;
  color: var(--color-primary, #0066cc);
  font: var(--text-caption, 14px/1.43 -0.224px);
  cursor: pointer;
  text-decoration: underline;
  padding: 4px 8px;
}

.btn-apple-danger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background-color: #ff3b30;
  color: var(--color-on-primary, #ffffff);
  border: none;
  border-radius: var(--rounded-pill, 9999px);
  padding: 11px 22px;
  font: var(--text-body, 17px/1.47 -0.374px);
  cursor: pointer;
  transition: transform 0.1s;
}
.btn-apple-danger:active { transform: scale(0.95); }
</style>