<template>
  <div class="approval-request-form">
    <h3>提交申请</h3>

    <div class="form-group">
      <label>申请类型</label>
      <select v-model="form.type" class="type-select">
        <option value="">请选择...</option>
        <option value="join_team">加入团队</option>
        <option value="private_space">创建私人空间</option>
        <option value="quota_extend">扩展配额</option>
        <option value="team_create">创建团队</option>
        <option value="storage_pool">申请存储池</option>
      </select>
    </div>

    <div class="form-group" v-if="form.type">
      <label>目标ID <span class="optional">(可选)</span></label>
      <input
        v-model="form.targetId"
        type="text"
        placeholder="输入目标资源ID"
        class="text-input"
      />
    </div>

    <div class="form-group" v-if="form.type">
      <label>申请理由 <span class="optional">(可选)</span></label>
      <textarea
        v-model="form.reason"
        placeholder="请输入申请理由..."
        rows="3"
        class="textarea"
      ></textarea>
    </div>

    <div class="form-actions">
      <button
        class="btn-submit"
        @click="handleSubmit"
        :disabled="submitting || !form.type"
      >
        {{ submitting ? '提交中...' : '提交申请' }}
      </button>
    </div>

    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <div v-if="success" class="success-message">
      申请提交成功！
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useApprovalStore, APPROVAL_TYPES } from '@/stores/approvalStore'

const emit = defineEmits(['submitted', 'error'])

const store = useApprovalStore()

const form = reactive({
  type: '',
  targetId: '',
  reason: ''
})

const submitting = ref(false)
const error = ref('')
const success = ref(false)

async function handleSubmit() {
  if (!form.type) return

  error.value = ''
  success.value = false
  submitting.value = true

  try {
    await store.createRequest({
      type: form.type,
      targetId: form.targetId || null,
      reason: form.reason || null,
      params: {}
    })

    success.value = true
    // 重置表单
    form.type = ''
    form.targetId = ''
    form.reason = ''

    emit('submitted')

    // 3秒后清除成功消息
    setTimeout(() => {
      success.value = false
    }, 3000)
  } catch (e) {
    error.value = e.message
    emit('error', e.message)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.approval-request-form {
  padding: var(--spacing-md);
  background: var(--color-surface-tile-3);
  border-radius: var(--radius-lg);
}

h3 {
  margin: 0 0 var(--spacing-md) 0;
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--color-body-on-dark);
}

.form-group {
  margin-bottom: var(--spacing-md);
}

.form-group label {
  display: block;
  margin-bottom: var(--space-xxs);
  font-size: 14px;
  color: var(--color-body-muted);
}

.optional {
  color: var(--color-body-muted);
  font-weight: normal;
}

.type-select,
.text-input,
.textarea {
  width: 100%;
  padding: var(--space-xs) var(--space-sm);
  background: var(--color-surface-tile-1);
  border: 1px solid var(--color-border-on-dark);
  border-radius: var(--radius-md);
  color: var(--color-body-on-dark);
  font-size: 14px;
  box-sizing: border-box;
  font-family: var(--font-family-text);
}

.type-select:focus,
.text-input:focus,
.textarea:focus {
  outline: none;
  border-color: var(--color-primary);
}

.textarea {
  resize: vertical;
}

.form-actions {
  margin-top: var(--spacing-lg);
}

.btn-submit {
  width: 100%;
  padding: var(--space-xs) var(--spacing-md);
  background: var(--color-primary);
  color: var(--color-on-primary);
  border: none;
  border-radius: var(--radius-pill);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: var(--transition-active);
}

.btn-submit:hover:not(:disabled) {
  background: var(--color-primary-focus);
}

.btn-submit:active:not(:disabled) {
  transform: scale(0.95);
}

.btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-message {
  margin-top: var(--space-sm);
  padding: var(--space-xs);
  background: var(--color-danger-subtle);
  color: var(--color-danger);
  border-radius: var(--radius-md);
  font-size: 14px;
}

.success-message {
  margin-top: var(--space-sm);
  padding: var(--space-xs);
  background: var(--color-success-subtle);
  color: var(--color-success);
  border-radius: var(--radius-md);
  font-size: 14px;
}
</style>
