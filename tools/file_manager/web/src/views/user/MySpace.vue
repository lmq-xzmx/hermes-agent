<template>
  <LifecycleProvider>
  <div class="my-space">
    <header class="my-space__header">
      <h1 class="my-space__title">我的空间</h1>
      <button @click="showApplyExpand = true" class="button-primary">
        申请扩容
      </button>
    </header>

    <div v-if="loading" class="my-space__loading">加载中...</div>

    <div v-else class="my-space__content">
      <!-- 我的私有空间 -->
      <section class="my-space__section">
        <div class="my-space__section-header">
          <h2 class="my-space__section-title">我的私有空间</h2>
        </div>

        <div class="space-card">
          <div class="space-card__info">
            <div class="space-card__name">{{ currentUser.username }} 的空间</div>
            <div class="space-card__meta">
              <span class="space-card__label">配额</span>
              <span class="space-card__value">{{ formatBytes(mySpace.committed_bytes) }}</span>
            </div>
            <div class="space-card__meta">
              <span class="space-card__label">已用</span>
              <span class="space-card__value">{{ formatBytes(mySpace.used_bytes) }}</span>
            </div>
            <div class="space-card__meta">
              <span class="space-card__label">剩余</span>
              <span class="space-card__value">{{ formatBytes(mySpace.available_bytes) }}</span>
            </div>
          </div>

          <div class="space-card__progress">
            <div class="progress-bar">
              <div
                class="progress-bar__fill"
                :class="getUsageClass(mySpace.used_bytes / mySpace.committed_bytes)"
                :style="{ width: Math.min(100, (mySpace.used_bytes / mySpace.committed_bytes) * 100) + '%' }"
              ></div>
            </div>
            <div class="progress-bar__text">
              {{ ((mySpace.used_bytes / mySpace.committed_bytes) * 100).toFixed(1) }}%
            </div>
          </div>

          <div v-if="mySpace.used_bytes > mySpace.committed_bytes * 0.9" class="space-card__warning">
            ⚠️ 空间使用率超过 90%，请及时清理或申请扩容
          </div>
        </div>
      </section>

      <!-- 加入的团队 -->
      <section class="my-space__section">
        <div class="my-space__section-header">
          <h2 class="my-space__section-title">加入的团队</h2>
        </div>

        <div v-if="teamSpaces.length === 0" class="my-space__empty">
          暂未加入任何团队
        </div>

        <div v-else class="team-list">
          <div v-for="team in teamSpaces" :key="team.id" class="team-card">
            <div class="team-card__header">
              <span class="team-card__name">{{ team.name }}</span>
              <span class="badge" :class="getStatusClass(team)">
                {{ getStatusText(team) }}
              </span>
            </div>

            <div class="team-card__quota">
              <div class="team-card__quota-row">
                <span>配额</span>
                <span>{{ formatBytes(team.committed_bytes) }}</span>
              </div>
              <div class="team-card__quota-row">
                <span>已用</span>
                <span>{{ formatBytes(team.used_bytes) }}</span>
              </div>
            </div>

            <div class="team-card__progress">
              <div class="progress-bar progress-bar--sm">
                <div
                  class="progress-bar__fill"
                  :class="getUsageClass(team.used_bytes / team.committed_bytes)"
                  :style="{ width: Math.min(100, (team.used_bytes / team.committed_bytes) * 100) + '%' }"
                ></div>
              </div>
            </div>

            <button @click="viewTeamDetail(team)" class="button-secondary button-secondary--sm">
              查看详情
            </button>
          </div>
        </div>
      </section>

      <!-- 申请记录 -->
      <section class="my-space__section">
        <div class="my-space__section-header">
          <h2 class="my-space__section-title">申请记录</h2>
        </div>

        <div v-if="requestHistory.length === 0" class="my-space__empty">
          暂无申请记录
        </div>

        <table v-else class="data-table">
          <thead>
            <tr>
              <th>申请类型</th>
              <th>申请内容</th>
              <th>状态</th>
              <th>申请时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="req in requestHistory" :key="req.id">
              <td>{{ req.type }}</td>
              <td>{{ req.content }}</td>
              <td>
                <span class="badge" :class="getRequestStatusClass(req.status)">
                  {{ req.status_text }}
                </span>
              </td>
              <td>{{ formatDate(req.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>

    <!-- 申请扩容弹窗 -->
    <div v-if="showApplyExpand" class="modal-overlay" @click.self="showApplyExpand = false">
      <div class="modal">
        <div class="modal__header">
          <h3 class="modal__title">申请扩容</h3>
          <button @click="showApplyExpand = false" class="modal__close">×</button>
        </div>
        <div class="modal__body">
          <div class="form-group">
            <label class="form-group__label">当前配额</label>
            <div class="form-group__value">
              {{ formatBytes(mySpace.committed_bytes) }}
            </div>
          </div>
          <div class="form-group">
            <label class="form-group__label">申请扩容至</label>
            <div class="quota-options">
              <button
                v-for="option in quotaOptions"
                :key="option.value"
                :class="['quota-option', { 'quota-option--selected': expandRequest.newQuota === option.value }]"
                @click="expandRequest.newQuota = option.value"
              >
                {{ option.label }}
              </button>
            </div>
          </div>
          <div class="form-group">
            <label class="form-group__label">申请理由</label>
            <textarea
              v-model="expandRequest.reason"
              placeholder="请输入申请扩容的理由..."
              rows="4"
              class="form-textarea"
            ></textarea>
          </div>
        </div>
        <div class="modal__footer">
          <button @click="showApplyExpand = false" class="button-secondary">取消</button>
          <button @click="submitExpandRequest" class="button-primary" :disabled="submitting">
            {{ submitting ? '提交中...' : '提交申请' }}
          </button>
        </div>
      </div>
    </div>
  </LifecycleProvider>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import LifecycleProvider from '@/components/lifecycle/LifecycleProvider.vue'

const loading = ref(true)
const submitting = ref(false)
const showApplyExpand = ref(false)

const currentUser = ref({
  username: 'current_user',
  id: 'u1'
})

const mySpace = ref({
  committed_bytes: 10 * 1024 * 1024 * 1024,
  used_bytes: 2 * 1024 * 1024 * 1024,
  available_bytes: 8 * 1024 * 1024 * 1024
})

const teamSpaces = ref([
  {
    id: 't1',
    name: '团队A',
    committed_bytes: 100 * 1024 * 1024 * 1024,
    used_bytes: 40 * 1024 * 1024 * 1024,
    status: 'normal'
  },
  {
    id: 't2',
    name: '团队B',
    committed_bytes: 50 * 1024 * 1024 * 1024,
    used_bytes: 45 * 1024 * 1024 * 1024,
    status: 'warning'
  }
])

const requestHistory = ref([
  {
    id: 'r1',
    type: '扩容申请',
    content: '申请从 10GB 扩容至 20GB',
    status: 'pending',
    status_text: '待审批',
    created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000)
  }
])

const quotaOptions = [
  { label: '20 GB', value: 20 * 1024 * 1024 * 1024 },
  { label: '50 GB', value: 50 * 1024 * 1024 * 1024 },
  { label: '100 GB', value: 100 * 1024 * 1024 * 1024 },
  { label: '200 GB', value: 200 * 1024 * 1024 * 1024 },
  { label: '500 GB', value: 500 * 1024 * 1024 * 1024 }
]

const expandRequest = ref({
  newQuota: 20 * 1024 * 1024 * 1024,
  reason: ''
})

function formatBytes(bytes) {
  if (bytes >= 1024 * 1024 * 1024 * 1024) {
    return (bytes / (1024 * 1024 * 1024 * 1024)).toFixed(2) + ' TB'
  }
  if (bytes >= 1024 * 1024 * 1024) {
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
  }
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

function formatDate(date) {
  return new Date(date).toLocaleDateString('zh-CN')
}

function getUsageClass(ratio) {
  if (ratio >= 0.95) return 'progress-bar__fill--critical'
  if (ratio >= 0.8) return 'progress-bar__fill--warning'
  return 'progress-bar__fill--normal'
}

function getStatusClass(team) {
  const ratio = team.used_bytes / team.committed_bytes
  if (ratio >= 0.95) return 'badge--danger'
  if (ratio >= 0.8) return 'badge--warning'
  return 'badge--success'
}

function getStatusText(team) {
  const ratio = team.used_bytes / team.committed_bytes
  if (ratio >= 0.95) return '严重'
  if (ratio >= 0.8) return '预警'
  return '正常'
}

function getRequestStatusClass(status) {
  if (status === 'approved') return 'badge--success'
  if (status === 'rejected') return 'badge--danger'
  return 'badge--warning'
}

function viewTeamDetail(team) {}

async function submitExpandRequest() {
  submitting.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 500))
    requestHistory.value.unshift({
      id: 'r' + Date.now(),
      type: '扩容申请',
      content: `申请从 ${formatBytes(mySpace.value.committed_bytes)} 扩容至 ${formatBytes(expandRequest.value.newQuota)}`,
      status: 'pending',
      status_text: '待审批',
      created_at: new Date()
    })
    showApplyExpand.value = false
    expandRequest.value = { newQuota: 20 * 1024 * 1024 * 1024, reason: '' }
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await new Promise(resolve => setTimeout(resolve, 300))
  loading.value = false
})
</script>

<style scoped>
/* === MySpace - 用户空间页面 === */

.my-space {
  padding: var(--spacing-lg);
  max-width: var(--content-max-width-universal);
  margin: 0 auto;
}

/* === Header === */
.my-space__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xl);
}

.my-space__title {
  font: var(--text-display-md);
  color: var(--color-ink);
  margin: 0;
}

/* === Loading === */
.my-space__loading {
  text-align: center;
  padding: var(--spacing-xxl);
  font: var(--text-body);
  color: var(--color-ink-muted-48);
}

/* === Content === */
.my-space__content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

/* === Section === */
.my-space__section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.my-space__section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.my-space__section-title {
  font: var(--text-body-strong);
  color: var(--color-ink);
  margin: 0;
}

/* === Empty State === */
.my-space__empty {
  padding: var(--spacing-xl);
  text-align: center;
  font: var(--text-body);
  color: var(--color-ink-muted-48);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
}

/* === Space Card === */
.space-card {
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.space-card__info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.space-card__name {
  font: var(--text-body-strong);
  color: var(--color-ink);
}

.space-card__meta {
  display: flex;
  justify-content: space-between;
  font: var(--text-caption);
}

.space-card__label {
  color: var(--color-ink-muted-48);
}

.space-card__value {
  color: var(--color-ink);
}

.space-card__progress {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.space-card__warning {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-warning-subtle);
  color: var(--color-warning-strong);
  border-radius: var(--radius-sm);
  font: var(--text-caption);
}

/* === Team List === */
.team-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--spacing-md);
}

/* === Team Card === */
.team-card {
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.team-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.team-card__name {
  font: var(--text-body-strong);
  color: var(--color-ink);
}

.team-card__quota {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xxs);
}

.team-card__quota-row {
  display: flex;
  justify-content: space-between;
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.team-card__progress {
  margin-top: var(--spacing-xs);
}

/* === Progress Bar === */
.progress-bar {
  height: var(--spacing-xs);
  background: var(--color-canvas-parchment);
  border-radius: var(--radius-xs);
  overflow: hidden;
}

.progress-bar--sm {
  height: 4px;
}

.progress-bar__fill {
  height: 100%;
  border-radius: var(--radius-xs);
  transition: width 0.3s;
}

.progress-bar__fill--normal { background: var(--color-success); }
.progress-bar__fill--warning { background: var(--color-warning); }
.progress-bar__fill--critical { background: var(--color-danger); }

.progress-bar__text {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
  min-width: 50px;
  text-align: right;
}

/* === Badge === */
.badge {
  display: inline-block;
  padding: var(--spacing-xxs) var(--spacing-sm);
  border-radius: var(--radius-pill);
  font: var(--text-caption);
}

.badge--success {
  background: var(--color-success-subtle);
  color: var(--color-success);
}

.badge--warning {
  background: var(--color-warning-subtle);
  color: var(--color-warning-strong);
}

.badge--danger {
  background: var(--color-danger-subtle);
  color: var(--color-danger-strong);
}

/* === Data Table === */
.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: var(--spacing-md);
  text-align: left;
  border-bottom: 1px solid var(--color-divider-soft);
}

.data-table th {
  font: var(--text-caption-strong);
  color: var(--color-ink-muted-48);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.data-table td {
  font: var(--text-body);
  color: var(--color-ink);
}

/* === Buttons === */
.button-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: var(--color-on-primary);
  border: none;
  border-radius: var(--radius-pill);
  padding: var(--spacing-sm) var(--spacing-md);
  font: var(--text-body);
  cursor: pointer;
  transition: transform 0.1s ease, opacity 0.15s ease;
}

.button-primary:active {
  transform: scale(0.95);
}

.button-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.button-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-pill);
  padding: var(--spacing-sm) var(--spacing-md);
  font: var(--text-body);
  cursor: pointer;
  transition: transform 0.1s ease, background 0.15s ease;
}

.button-secondary:active {
  transform: scale(0.95);
}

.button-secondary--sm {
  font: var(--text-caption);
  padding: var(--spacing-xxs) var(--spacing-sm);
}

/* === Modal Overlay === */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--color-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal-backdrop);
}

/* === Modal === */
.modal {
  background: var(--color-canvas);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow: auto;
}

.modal__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-divider-soft);
}

.modal__title {
  font: var(--text-body-strong);
  margin: 0;
}

.modal__close {
  background: none;
  border: none;
  font-size: 24px;
  color: var(--color-ink-muted-48);
  cursor: pointer;
}

.modal__body {
  padding: var(--spacing-lg);
}

.modal__footer {
  display: flex;
  gap: var(--spacing-sm);
  justify-content: flex-end;
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-divider-soft);
}

/* === Form Group === */
.form-group {
  margin-bottom: var(--spacing-md);
}

.form-group__label {
  display: block;
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
  margin-bottom: var(--spacing-xxs);
}

.form-group__value {
  font: var(--text-body-strong);
  color: var(--color-ink);
}

.form-textarea {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  font: var(--text-body);
  color: var(--color-ink);
  resize: vertical;
  box-sizing: border-box;
}

.form-textarea:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

/* === Quota Options === */
.quota-options {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.quota-option {
  padding: var(--spacing-xxs) var(--spacing-sm);
  background: var(--color-canvas-parchment);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  font: var(--text-caption);
  color: var(--color-ink);
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease;
}

.quota-option:hover {
  background: var(--color-canvas);
}

.quota-option--selected {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-on-primary);
}
</style>