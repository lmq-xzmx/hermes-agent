<template>
  <div class="file-view">
    <!-- Toolbar -->
    <FileToolbar
      :current-path="currentPath"
      :breadcrumbs="breadcrumbs"
      :view-mode="viewMode"
      :search-query="searchQuery"
      :can-go-back="canGoBack"
      :can-go-forward="canGoForward"
      :can-upload="canUpload"
      :can-share="canShare"
      :can-paste="canPaste"
      :can-write="canWrite"
      @navigate="navigateToBreadcrumb"
      @go-back="goBack"
      @go-forward="goForward"
      @go-up="goUp"
      @refresh="refresh"
      @upload="triggerUpload"
      @share="shareSelected"
      @paste="pasteFiles"
      @toggle-view="setViewMode"
      @search="onSearchInput"
      @clear-search="clearSearch"
      @toggle-floating="toggleFloatingWindow"
    />

    <!-- Hidden file input -->
    <input type="file" ref="fileInput" multiple style="display:none" @change="handleFileUpload">

    <!-- Empty State -->
    <FileEmptyState
      :type="emptyGuidanceType"
      :show="showEmptyGuidance"
      :search-query="searchQuery"
      :filtered-files="filteredFiles"
      :total-files="files.length"
      :spaces="spaceStore.spaces"
      :user-role="authStore.userRole"
      :can-upload="canUpload"
      @go-to-spaces="goToSpaces"
      @select-space="selectSpace"
      @upload="triggerUpload"
      @create-folder="createFolder"
    />

    <!-- List View -->
    <FileListView
      v-show="viewMode === 'list'"
      :files="filteredFiles"
      :selected-paths="selectedFiles"
      :all-selected="isAllSelected"
      @row-click="onRowClick"
      @row-contextmenu="onContextMenu"
      @checkbox-change="toggleFileSelection"
      @select-all="toggleSelectAll"
      @drag-start="onDragStart"
      @drag-over="onDragOver"
      @drag-leave="onDragLeave"
      @drop="onDrop"
      @action="onFileAction"
    />

    <!-- Grid View -->
    <FileGridView
      v-show="viewMode === 'grid'"
      :files="filteredFiles"
      :selected-paths="selectedFiles"
      :all-selected="isAllSelected"
      @row-click="onGridItemClick"
      @row-contextmenu="onContextMenu"
      @checkbox-change="toggleFileSelection"
      @select-all="toggleSelectAll"
      @drag-start="onDragStart"
      @drag-over="onDragOver"
      @drag-leave="onDragLeave"
      @drop="onDrop"
      @action="onFileAction"
    />

    <!-- Selection Rectangle -->
    <FileSelectionRect :rect="selectionRect" />

    <!-- Multi-Selection Action Bar -->
    <FileMultiSelectBar
      v-if="selectedFiles.size > 0"
      :selected-count="selectedFiles.size"
      :can-share="canShare"
      :can-paste="canPaste"
      :can-write="canWrite"
      :can-delete="canDelete"
      @share="shareSelected"
      @download="downloadSelected"
      @paste="pasteFiles"
      @delete="deleteSelected"
      @clear-selection="clearSelection"
    />

    <!-- Context Menu -->
    <FileContextMenu
      ref="contextMenuRef"
      :can-paste="canPaste"
      :can-write="canWrite"
      :can-delete="canDelete"
      :can-rename="canWrite"
      @action="onContextAction"
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
import { useLifecycleStore } from '../stores/lifecycleStore.js'
import FileContextMenu from '../components/FileContextMenu.vue'
import PreviewModal from '../components/PreviewModal.vue'
import FileToolbar from '../components/FileToolbar.vue'
import FileListView from '../components/FileListView.vue'
import FileGridView from '../components/FileGridView.vue'
import FileEmptyState from '../components/FileEmptyState.vue'
import FileSelectionRect from '../components/FileSelectionRect.vue'
import FileMultiSelectBar from '../components/FileMultiSelectBar.vue'
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
const lifecycleStore = useLifecycleStore()
const router = useRouter()
const { onFirstFileUploaded, onFileUploaded } = useGuidanceTrigger()

// Computed: get currentSpaceId from store
const currentSpaceId = computed(() => spaceStore.currentSpaceId)

// Computed: 文件操作权限
const currentSpace = computed(() => spaceStore.selectedSpace)
const isAdmin = computed(() => authStore.userRole === 'admin')
const mySpaceRole = computed(() => currentSpace.value?.my_role || null)

// 是否为空间成员 (owner/member 可以读写, viewer 只读, guest/guest 只能读)
const canWrite = computed(() => {
  if (isAdmin.value) return true
  const role = mySpaceRole.value
  return role === 'owner' || role === 'member'
})

// 是否可以删除文件 (owner/member 可以, viewer/guest 不行)
const canDelete = computed(() => {
  if (isAdmin.value) return true
  const role = mySpaceRole.value
  return role === 'owner' || role === 'member'
})

// 是否可以创建文件夹
const canCreateFolder = computed(() => canWrite.value)

// 是否可以上传文件
const canUpload = computed(() => canWrite.value)

// 是否可以分享
const canShare = computed(() => {
  if (isAdmin.value) return true
  return !!mySpaceRole.value // 任何成员都可以分享
})

const files = ref([])
const selectedFiles = ref(new Set())
const viewMode = ref('list')
const loading = ref(false)
const fileInput = ref(null)
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
  onPreview: () => {
    const file = getFirstSelectedFile()
    if (file && !file.is_directory) {
      openPreview(file)
    }
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
    emit('show-toast', { type: '粘贴失败', message: err.message })
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

// Handle file actions from list/grid view
function onFileAction(action, path) {
  const file = files.value.find(f => f.path === path)
  if (!file) return

  switch (action) {
    case 'finder':
      openInFinder(path)
      break
    case 'delete':
      deleteItem(path, file.is_directory ? 'directory' : 'file')
      break
    case 'share':
      shareItem(path)
      break
  }
}

// Context menu handlers
function onContextAction(actionId) {
  const selectedFile = getFirstSelectedFile()
  if (!selectedFile) return

  switch (actionId) {
    case 'open':
      onContextOpen(selectedFile)
      break
    case 'open-in-finder':
      onContextOpenInFinder(selectedFile)
      break
    case 'rename':
      onContextRename(selectedFile)
      break
    case 'copy':
      onContextCopy(selectedFile)
      break
    case 'cut':
      onContextCut(selectedFile)
      break
    case 'paste':
      onContextPaste(selectedFile)
      break
    case 'share':
      onContextShare(selectedFile)
      break
    case 'delete':
      onContextDelete(selectedFile)
      break
    case 'info':
      showFileInfo(selectedFile)
      break
  }
}

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
  const targetPath = targetFolder.path + '/' + sourceName

  // 同一目录内移动/复制无效
  if (sourcePath === targetFolder.path || sourcePath === targetPath) return

  // 判断是移动还是复制（Alt/Mac: metaKey, Windows/Linux: ctrlKey）
  const isCopy = event.altKey || event.ctrlKey || event.metaKey

  try {
    if (isCopy) {
      await api.copyFile(currentSpaceId.value, sourcePath, targetPath)
      emit('show-toast', { type: 'success', title: '已复制', message: `"${sourceName}" 已复制到目标文件夹` })
    } else {
      await api.moveFile(currentSpaceId.value, null, sourcePath, targetPath)
      emit('show-toast', { type: 'success', title: '已移动', message: `"${sourceName}" 已移动` })
    }
    loadFiles(props.currentPath)
  } catch (err) {
    emit('show-toast', { type: 'error', title: isCopy ? '复制失败' : '移动失败', message: err.message })
  }
}

function showFileInfo(file) {
  const info = `名称: ${file.name}\n类型: ${file.is_directory ? '文件夹' : '文件'}\n路径: ${file.path}\n大小: ${file.size || '-'}}\n修改: ${file.modified || '-'}`
  alert(info)
}
</script>

<style scoped>
.file-view {
  display: flex;
  flex-direction: column;
  flex: 1;
  height: 100%;
  background: transparent;
  overflow: auto;
}
</style>
