<template>
  <div class="todo-entry">
    <div class="todo-entry__header">
      <div class="todo-entry__title-row">
        <h3 class="todo-entry__title">{{ title }}</h3>
        <span v-if="tasks.length > 0" class="todo-entry__badge">{{ tasks.length }}</span>
      </div>
      <button
        v-if="showRefresh"
        class="todo-entry__refresh"
        @click="$emit('refresh')"
        :disabled="loading"
      >
        <span class="todo-entry__refresh-icon" :class="{ 'todo-entry__refresh-icon--spinning': loading }">🔄</span>
      </button>
    </div>

    <div v-if="loading" class="todo-entry__loading">
      <div class="todo-entry__spinner"></div>
      <span>加载中...</span>
    </div>

    <div v-else-if="tasks.length === 0" class="todo-entry__empty">
      <span class="todo-entry__empty-icon">📋</span>
      <span>{{ emptyText }}</span>
    </div>

    <div v-else class="todo-entry__list">
      <div
        v-for="task in tasks"
        :key="task.id"
        class="todo-entry__item"
      >
        <div class="todo-entry__item-icon">
          {{ getTaskIcon(task.type) }}
        </div>
        <div class="todo-entry__item-content">
          <div class="todo-entry__item-header">
            <span class="todo-entry__item-type">{{ getTaskTypeName(task.type) }}</span>
            <span class="todo-entry__item-time">{{ formatTime(task.created_at) }}</span>
          </div>
          <div class="todo-entry__item-body">
            <span class="todo-entry__item-applicant">{{ task.applicant_name || task.requester_name || '未知申请人' }}</span>
            <span v-if="task.team_name" class="todo-entry__item-team">{{ task.team_name }}</span>
          </div>
          <p v-if="task.reason" class="todo-entry__item-reason">{{ task.reason }}</p>
        </div>
        <div class="todo-entry__item-actions" v-if="showActions">
          <button
            class="todo-entry__btn todo-entry__btn--detail"
            @click="$emit('view', task)"
            :title="detailLabel"
          >
            {{ detailLabel }}
          </button>
          <button
            class="todo-entry__btn todo-entry__btn--approve"
            @click="$emit('approve', task)"
            :title="approveLabel"
          >
            {{ approveLabel }}
          </button>
          <button
            class="todo-entry__btn todo-entry__btn--reject"
            @click="$emit('reject', task)"
            :title="rejectLabel"
          >
            {{ rejectLabel }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="hasMore && tasks.length > 0" class="todo-entry__footer">
      <button class="todo-entry__more" @click="$emit('load-more')">
        加载更多
      </button>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  title: {
    type: String,
    default: '待办任务'
  },
  tasks: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  showRefresh: {
    type: Boolean,
    default: true
  },
  showActions: {
    type: Boolean,
    default: true
  },
  emptyText: {
    type: String,
    default: '暂无待办任务'
  },
  detailLabel: {
    type: String,
    default: '查看'
  },
  approveLabel: {
    type: String,
    default: '批准'
  },
  rejectLabel: {
    type: String,
    default: '拒绝'
  },
  hasMore: {
    type: Boolean,
    default: false
  }
})

defineEmits(['refresh', 'view', 'approve', 'reject', 'load-more'])

const typeIconMap = {
  'team_join': '👥',
  'team_member_exit': '🚪',
  'private_space': '📁',
  'quota_extend': '📈',
  'storage_pool': '💾',
  'team_create': '➕'
}

const typeNameMap = {
  'team_join': '申请加入团队',
  'team_member_exit': '成员退出申请',
  'private_space': '私人空间申请',
  'quota_extend': '配额扩容申请',
  'storage_pool': '存储池申请',
  'team_create': '创建团队申请'
}

function getTaskIcon(type) {
  return typeIconMap[type] || '📋'
}

function getTaskTypeName(type) {
  return typeNameMap[type] || type || '未知类型'
}

function formatTime(time) {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins} 分钟前`
  if (diffHours < 24) return `${diffHours} 小时前`
  if (diffDays < 7) return `${diffDays} 天前`
  return date.toLocaleDateString()
}
</script>

<style scoped>
/* ============================================
   TodoEntry - 待办任务入口组件
   Apple Design System + BEM
   ============================================ */

.todo-entry {
  /* Layout */
  background: var(--color-surface-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);

  /* Visual */
  box-shadow: var(--shadow-elevation-1);
}

/* ============================================
   Element: todo-entry__header
   ============================================ */
.todo-entry__header {
  /* Layout */
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
}

.todo-entry__title-row {
  /* Layout */
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.todo-entry__title {
  /* Typography */
  font: var(--text-headline);
  color: var(--color-ink-primary);
  margin: 0;
}

.todo-entry__badge {
  /* Box Model */
  padding: 2px 8px;
  border-radius: var(--radius-full);

  /* Visual */
  background: var(--color-danger);
  color: var(--color-white);

  /* Typography */
  font: var(--text-caption);
  font-weight: 600;
}

.todo-entry__refresh {
  /* Box Model */
  padding: var(--spacing-xs);
  border: none;
  border-radius: var(--radius-md);

  /* Visual */
  background: transparent;
  cursor: pointer;

  /* Interactive */
  transition: background 0.2s ease;
}

.todo-entry__refresh:hover {
  background: var(--color-surface-tertiary);
}

.todo-entry__refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.todo-entry__refresh-icon {
  /* Layout */
  display: inline-block;

  /* Typography */
  font-size: 16px;
}

.todo-entry__refresh-icon--spinning {
  /* Animation */
  animation: todo-entry__spin 1s linear infinite;
}

@keyframes todo-entry__spin {
  to { transform: rotate(360deg); }
}

/* ============================================
   Element: todo-entry__loading
   ============================================ */
.todo-entry__loading {
  /* Layout */
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
  gap: var(--spacing-sm);

  /* Typography */
  font: var(--text-body);
  color: var(--color-ink-muted-48);
}

.todo-entry__spinner {
  /* Box Model */
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-surface-tertiary);
  border-top-color: var(--color-primary);
  border-radius: var(--radius-full);

  /* Animation */
  animation: todo-entry__spin 0.8s linear infinite;
}

/* ============================================
   Element: todo-entry__empty
   ============================================ */
.todo-entry__empty {
  /* Layout */
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
  gap: var(--spacing-sm);

  /* Typography */
  font: var(--text-body);
  color: var(--color-ink-muted-48);
}

.todo-entry__empty-icon {
  /* Typography */
  font-size: 32px;
  opacity: 0.5;
}

/* ============================================
   Element: todo-entry__list
   ============================================ */
.todo-entry__list {
  /* Layout */
  display: flex;
  flex-direction: column;
}

/* ============================================
   Element: todo-entry__item
   ============================================ */
.todo-entry__item {
  /* Layout */
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-md);
  padding: var(--spacing-md) 0;
  border-bottom: 1px solid var(--color-surface-tertiary);

  /* Interactive */
  transition: background 0.15s ease;
}

.todo-entry__item:last-child {
  border-bottom: none;
}

.todo-entry__item:hover {
  background: var(--color-surface-tint);
  margin: 0 calc(-1 * var(--spacing-sm));
  padding-left: var(--spacing-sm);
  padding-right: var(--spacing-sm);
  border-radius: var(--radius-md);
}

.todo-entry__item-icon {
  /* Box Model */
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);

  /* Visual */
  background: var(--color-surface-tertiary);

  /* Typography */
  font-size: 18px;
  flex-shrink: 0;
}

.todo-entry__item-content {
  /* Layout */
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xxs);
}

.todo-entry__item-header {
  /* Layout */
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
}

.todo-entry__item-type {
  /* Typography */
  font: var(--text-subheadline);
  font-weight: 600;
  color: var(--color-ink-primary);
}

.todo-entry__item-time {
  /* Typography */
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.todo-entry__item-body {
  /* Layout */
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.todo-entry__item-applicant {
  /* Typography */
  font: var(--text-body);
  color: var(--color-ink-secondary);
}

.todo-entry__item-team {
  /* Box Model */
  padding: 1px 6px;
  border-radius: var(--radius-sm);

  /* Visual */
  background: var(--color-surface-tertiary);

  /* Typography */
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.todo-entry__item-reason {
  /* Box Model */
  margin: var(--spacing-xxs) 0 0;
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);

  /* Visual */
  background: var(--color-surface-tint);

  /* Typography */
  font: var(--text-caption);
  color: var(--color-ink-secondary);
}

/* ============================================
   Element: todo-entry__item-actions
   ============================================ */
.todo-entry__item-actions {
  /* Layout */
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  flex-shrink: 0;
}

.todo-entry__btn {
  /* Box Model */
  padding: var(--spacing-xs) var(--spacing-sm);
  border: none;
  border-radius: var(--radius-pill);
  font: var(--text-caption);

  /* Visual */
  cursor: pointer;

  /* Interactive */
  transition: all 0.15s ease;
}

.todo-entry__btn--detail {
  /* Visual */
  background: var(--color-surface-tertiary);
  color: var(--color-ink-secondary);
}

.todo-entry__btn--detail:hover {
  background: var(--color-surface-strong);
}

.todo-entry__btn--approve {
  /* Visual */
  background: var(--color-success);
  color: var(--color-white);
}

.todo-entry__btn--approve:hover {
  filter: brightness(1.1);
}

.todo-entry__btn--reject {
  /* Visual */
  background: var(--color-danger);
  color: var(--color-white);
}

.todo-entry__btn--reject:hover {
  filter: brightness(1.1);
}

/* ============================================
   Element: todo-entry__footer
   ============================================ */
.todo-entry__footer {
  /* Layout */
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-surface-tertiary);
  text-align: center;
}

.todo-entry__more {
  /* Box Model */
  padding: var(--spacing-xs) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  background: transparent;

  /* Typography */
  font: var(--text-caption);
  color: var(--color-ink-secondary);

  /* Visual */
  cursor: pointer;

  /* Interactive */
  transition: all 0.15s ease;
}

.todo-entry__more:hover {
  background: var(--color-surface-tertiary);
  border-color: var(--color-border-strong);
}
</style>