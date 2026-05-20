<template>
  <Transition name="fade">
    <div v-if="visible" class="shortcut-hints-overlay" @click.self="close">
      <div class="shortcut-hints-panel">
        <div class="shortcut-hints-header">
          <h3>键盘快捷键</h3>
          <button class="close-btn" @click="close">×</button>
        </div>
        <div class="shortcut-hints-content">
          <div v-for="group in shortcutGroups" :key="group.title" class="shortcut-group">
            <h4>{{ group.title }}</h4>
            <div v-for="item in group.items" :key="item.name" class="shortcut-item">
              <span class="shortcut-keys">
                <kbd v-for="(key, idx) in item.keys" :key="idx">{{ key }}</kbd>
              </span>
              <span class="shortcut-desc">{{ item.description }}</span>
            </div>
          </div>
        </div>
        <div class="shortcut-hints-footer">
          <span class="platform-hint">{{ isMac ? '⌘ = Command' : '^ = Control' }}</span>
          <span class="dismiss-hint">按 <kbd>Esc</kbd> 关闭</span>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script>
import { computed, onMounted, onUnmounted } from 'vue'
import { useKeyboardShortcuts, SHORTCUTS } from './useKeyboardShortcuts.js'

export default {
  name: 'ShortcutHints',
  props: {
    visible: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['close'],
  setup(props, { emit }) {
    const isMac = computed(() => navigator.platform.toUpperCase().indexOf('MAC') >= 0)

    // 快捷键分组
    const shortcutGroups = computed(() => [
      {
        title: '文件操作',
        items: [
          { name: '打开', keys: ['Enter'], description: '打开文件或文件夹' },
          { name: '重命名', keys: ['F2'], description: '重命名选中项' },
          { name: '删除', keys: [isMac.value ? '⌘' : 'Ctrl', '⌫'], description: '删除选中项' },
          { name: '复制', keys: [isMac.value ? '⌘' : 'Ctrl', 'C'], description: '复制选中项' },
          { name: '剪切', keys: [isMac.value ? '⌘' : 'Ctrl', 'X'], description: '剪切选中项' },
          { name: '粘贴', keys: [isMac.value ? '⌘' : 'Ctrl', 'V'], description: '粘贴' },
          { name: '复制到当前', keys: [isMac.value ? '⌘' : 'Ctrl', 'D'], description: '复制文件到当前目录' },
        ],
      },
      {
        title: '选择',
        items: [
          { name: '全选', keys: [isMac.value ? '⌘' : 'Ctrl', 'A'], description: '全选所有文件' },
          { name: '取消选择', keys: ['Esc'], description: '取消当前选择' },
          { name: '向上', keys: ['↑'], description: '选择上一个文件' },
          { name: '向下', keys: ['↓'], description: '选择下一个文件' },
          { name: '向左', keys: ['←'], description: '进入上级目录' },
          { name: '向右', keys: ['→'], description: '进入目录或选择下一个' },
        ],
      },
      {
        title: '新建',
        items: [
          { name: '新建文件夹', keys: [isMac.value ? '⌘' : 'Ctrl', '⇧', 'N'], description: '创建新文件夹' },
          { name: '新建文件', keys: [isMac.value ? '⌘' : 'Ctrl', 'N'], description: '创建新文件' },
        ],
      },
      {
        title: '视图',
        items: [
          { name: '预览', keys: ['Space'], description: '预览选中文件' },
          { name: '详情', keys: [isMac.value ? '⌘' : 'Ctrl', 'I'], description: '显示详情信息' },
          { name: '返回', keys: ['⌫'], description: '返回上级目录' },
        ],
      },
      {
        title: '窗口',
        items: [
          { name: '关闭', keys: [isMac.value ? '⌘' : 'Ctrl', 'W'], description: '关闭当前窗口/标签' },
          { name: '设置', keys: [isMac.value ? '⌘' : 'Ctrl', ','], description: '打开偏好设置' },
        ],
      },
    ])

    // ESC 关闭
    const { onEscape } = useKeyboardShortcuts({
      onEscape: () => emit('close'),
    })

    function close() {
      emit('close')
    }

    return {
      isMac,
      shortcutGroups,
      close,
    }
  },
}
</script>

