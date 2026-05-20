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

