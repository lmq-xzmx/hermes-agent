<template>
  <component
    :is="iconComponent"
    :size="size"
    :color="iconColor"
    :stroke-width="strokeWidth"
    :class="iconClass"
  />
</template>

<script setup>
import { computed } from 'vue'
import {
  // Navigation
  FileText,
  Users,
  Rocket,
  Database,
  Brain,
  Trash2,
  LogOut,
  Server,
  BookOpen,
  // File Types
  File,
  FileImage,
  FileVideo,
  FileAudio,
  FileCode,
  FileArchive,
  // Actions
  Plus,
  Minus,
  X,
  Check,
  Search,
  RefreshCw,
  Upload,
  Download,
  Share,
  Copy,
  Edit,
  Trash,
  FolderOpen,
  Eye,
  EyeOff,
  Settings,
  Menu,
  ChevronRight,
  ChevronDown,
  ChevronLeft,
  ChevronUp,
  TrendingUp,
  // View Toggle
  LayoutList,
  LayoutGrid,
  // Status
  AlertTriangle,
  Info,
  CheckCircle,
  XCircle,
  Loader,
  // Misc
  Palette,
  Moon,
  Sun,
  FolderPlus,
  Folder
} from 'lucide-vue-next'

const props = defineProps({
  /** 图标名称 - 对应 Lucide icon */
  name: {
    type: String,
    required: true
  },
  /** 图标尺寸 */
  size: {
    type: [Number, String],
    default: 18
  },
  /** 图标颜色 - 传入时优先使用 */
  color: {
    type: String,
    default: ''
  },
  /** 是否使用彩色图标 */
  colored: {
    type: Boolean,
    default: true
  },
  /** 线条粗细 */
  strokeWidth: {
    type: [Number, String],
    default: 2
  },
  /** 自定义类名 */
  class: {
    type: String,
    default: ''
  }
})

// 彩色图标映射表
const colorMap = {
  // 蓝色系 - 主色
  'users': '#0066cc',
  'team': '#0066cc',
  'teams': '#0066cc',
  'folder': '#0066cc',
  'folder-open': '#0066cc',
  'folder-plus': '#0066cc',
  'file': '#86868b',
  'files': '#86868b',
  'file-generic': '#86868b',

  // 紫色系 - 空间
  'space': '#5e5ce6',
  'spaces': '#5e5ce6',
  'rocket': '#5e5ce6',
  'pool': '#5e5ce6',
  'pools': '#5e5ce6',
  'database': '#5e5ce6',

  // 绿色系 - 成功/知识
  'knowledge': '#34c759',
  'brain': '#34c759',
  'book-open': '#34c759',
  'success': '#34c759',
  'check': '#34c759',
  'check-circle': '#34c759',

  // 黄色/橙色系 - 警告
  'warning': '#ff9500',
  'info': '#ff9500',
  'alert-triangle': '#ff9500',

  // 红色系 - 危险/删除
  'danger': '#ff3b30',
  'error': '#ff3b30',
  'x-circle': '#ff3b30',
  'trash': '#ff3b30',
  'delete': '#ff3b30',

  // 青色系 - 服务器/状态
  'server': '#30d5c8',
  'trending-up': '#30d5c8',

  // 灰蓝色 - 其他
  'search': '#86868b',
  'settings': '#86868b',
  'refresh': '#86868b',
  'upload': '#0071e3',
  'download': '#0071e3',
  'share': '#0071e3',
  'copy': '#0071e3',

  // 文件类型
  'file-image': '#ff9500',
  'file-video': '#af52de',
  'file-audio': '#ff2d55',
  'file-code': '#5ac8fa',
  'file-archive': '#ff9500',

  // 操作类图标 - 蓝灰色系
  'plus': '#0066cc',
  'minus': '#86868b',
  'close': '#86868b',
  'edit': '#0071e3',
  'eye': '#0071e3',
  'eye-off': '#86868b',
  'menu': '#86868b',

  // 导航箭头
  'chevron-right': '#86868b',
  'chevron-down': '#86868b',
  'chevron-left': '#86868b',
  'chevron-up': '#86868b',
  'arrow-left': '#86868b',
  'arrow-right': '#86868b',
  'arrow-up': '#86868b',
  'arrow-down': '#86868b',

  // 视图切换
  'list': '#86868b',
  'grid': '#86868b',

  // 状态加载
  'loading': '#0066cc',

  // 杂项图标
  'theme': '#5e5ce6',
  'palette': '#5e5ce6',
  'moon': '#5e5ce6',
  'sun': '#ff9500',
  'avatar': '#86868b',
  'log-out': '#86868b',
  'folder-closed': '#86868b',
}

const iconMap = {
  // Navigation
  'file': FileText,
  'files': FileText,
  'team': Users,
  'teams': Users,
  'users': Users,
  'rocket': Rocket,
  'space': Rocket,
  'spaces': Rocket,
  'pool': Database,
  'pools': Database,
  'database': Database,
  'brain': Brain,
  'knowledge': Brain,
  'trash': Trash2,
  'server': Server,
  'book-open': BookOpen,
  // Actions
  'plus': Plus,
  'minus': Minus,
  'close': X,
  'check': Check,
  'search': Search,
  'refresh': RefreshCw,
  'upload': Upload,
  'download': Download,
  'share': Share,
  'copy': Copy,
  'edit': Edit,
  'delete': Trash,
  'folder': FolderOpen,
  'folder-open': FolderOpen,
  'folder-plus': FolderPlus,
  'eye': Eye,
  'eye-off': EyeOff,
  'settings': Settings,
  'menu': Menu,
  'chevron-right': ChevronRight,
  'chevron-down': ChevronDown,
  'chevron-left': ChevronLeft,
  'chevron-up': ChevronUp,
  'chevron-right': ChevronRight,
  'trending-up': TrendingUp,
  // View Toggle
  'list': LayoutList,
  'grid': LayoutGrid,
  // Status
  'warning': AlertTriangle,
  'info': Info,
  'success': CheckCircle,
  'error': XCircle,
  'loading': Loader,
  // Misc
  'theme': Palette,
  'palette': Palette,
  'logout': LogOut,
  'log-out': LogOut,
  'avatar': Users,
  'moon': Moon,
  'sun': Sun,
  // File Types
  'file-generic': File,
  'file-image': FileImage,
  'file-video': FileVideo,
  'file-audio': FileAudio,
  'file-code': FileCode,
  'file-archive': FileArchive,
  // Arrow Navigation
  'arrow-left': ChevronLeft,
  'arrow-right': ChevronRight,
  'arrow-up': ChevronUp,
  'arrow-down': ChevronRight,
  // Folder
  'folder-closed': Folder
}

const iconComponent = computed(() => {
  return iconMap[props.name] || File
})

// 计算图标颜色
const iconColor = computed(() => {
  // 如果显式传入了 color，优先使用
  if (props.color) return props.color
  // 如果启用了 colored 模式，使用颜色映射
  if (props.colored) return colorMap[props.name] || '#86868b'
  // 默认使用 currentColor（继承父元素颜色）
  return 'currentColor'
})

const iconClass = computed(() => props.class)
</script>

<style scoped>
/* Icon uses currentColor by default, styled via parent */
/* Add colored class support via CSS variable */
</style>
