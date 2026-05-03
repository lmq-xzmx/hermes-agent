<template>
  <LifecycleProvider>
  <div class="space-request">
    <header class="page-header">
      <h1>申请新空间</h1>
    </header>

    <div class="request-content">
      <!-- 步骤指示器 -->
      <div class="steps-indicator">
        <div :class="['step', { active: currentStep >= 1, completed: currentStep > 1 }]">
          <div class="step-number">1</div>
          <div class="step-label">选择类型</div>
        </div>
        <div class="step-line"></div>
        <div :class="['step', { active: currentStep >= 2, completed: currentStep > 2 }]">
          <div class="step-number">2</div>
          <div class="step-label">填写信息</div>
        </div>
        <div class="step-line"></div>
        <div :class="['step', { active: currentStep >= 3 }]">
          <div class="step-number">3</div>
          <div class="step-label">提交申请</div>
        </div>
      </div>

      <!-- 步骤1: 选择空间类型 -->
      <div v-show="currentStep === 1" class="step-content">
        <h2>选择空间类型</h2>
        <div class="space-type-options">
          <label :class="['type-card', { selected: request.space_type === 'team' }]">
            <input v-model="request.space_type" type="radio" value="team" />
            <div class="type-icon">👔</div>
            <div class="type-name">团队空间</div>
            <div class="type-desc">适用于多人协作，可分配配额给团队成员</div>
            <div class="type-features">
              <span class="feature">多成员协作</span>
              <span class="feature">配额管理</span>
              <span class="feature">权限控制</span>
            </div>
          </label>

          <label :class="['type-card', { selected: request.space_type === 'personal' }]">
            <input v-model="request.space_type" type="radio" value="personal" />
            <div class="type-icon">👤</div>
            <div class="type-name">私人空间</div>
            <div class="type-desc">仅自己使用，适合个人文件存储</div>
            <div class="type-features">
              <span class="feature">专属配额</span>
              <span class="feature">独立使用</span>
              <span class="feature">简单管理</span>
            </div>
          </label>
        </div>

        <div class="step-actions">
          <button @click="nextStep" class="btn btn-primary" :disabled="!request.space_type">
            下一步
          </button>
        </div>
      </div>

      <!-- 步骤2: 填写信息 -->
      <div v-show="currentStep === 2" class="step-content">
        <h2>填写申请信息</h2>

        <div class="form-section">
          <div class="form-group">
            <label>空间名称 <span class="required">*</span></label>
            <input
              v-model="request.space_name"
              type="text"
              placeholder="输入空间名称"
              :class="{ error: errors.space_name }"
            />
            <span v-if="errors.space_name" class="error-text">{{ errors.space_name }}</span>
          </div>

          <div class="form-group">
            <label>申请配额 <span class="required">*</span></label>
            <div class="quota-selector">
              <div class="quota-range">
                可申请: {{ formatBytes(quotaRange.min) }} - {{ formatBytes(quotaRange.max) }}
              </div>
              <input
                v-model.number="request.quota_gb"
                type="range"
                :min="quotaRange.min / (1024 * 1024 * 1024)"
                :max="quotaRange.max / (1024 * 1024 * 1024)"
                step="1"
              />
              <div class="quota-value">
                <input
                  v-model.number="request.quota_gb"
                  type="number"
                  :min="quotaRange.min / (1024 * 1024 * 1024)"
                  :max="quotaRange.max / (1024 * 1024 * 1024)"
                />
                <span>GB</span>
              </div>
            </div>
            <div class="quota-presets">
              <button
                v-for="preset in quotaPresets"
                :key="preset"
                :class="['preset-btn', { selected: request.quota_gb === preset }]"
                @click="request.quota_gb = preset"
              >
                {{ preset }} GB
              </button>
            </div>
          </div>

          <div class="form-group">
            <label>申请理由 <span class="required">*</span></label>
            <textarea
              v-model="request.reason"
              placeholder="请详细说明申请空间的原因和用途..."
              rows="5"
              :class="{ error: errors.reason }"
            ></textarea>
            <span v-if="errors.reason" class="error-text">{{ errors.reason }}</span>
          </div>
        </div>

        <div class="step-actions">
          <button @click="prevStep" class="btn btn-secondary">上一步</button>
          <button @click="nextStep" class="btn btn-primary">下一步</button>
        </div>
      </div>

      <!-- 步骤3: 确认提交 -->
      <div v-show="currentStep === 3" class="step-content">
        <h2>确认申请信息</h2>

        <div class="review-section">
          <div class="review-item">
            <div class="review-label">空间类型</div>
            <div class="review-value">{{ request.space_type === 'team' ? '团队空间' : '私人空间' }}</div>
          </div>
          <div class="review-item">
            <div class="review-label">空间名称</div>
            <div class="review-value">{{ request.space_name }}</div>
          </div>
          <div class="review-item">
            <div class="review-label">申请配额</div>
            <div class="review-value">{{ request.quota_gb }} GB</div>
          </div>
          <div class="review-item">
            <div class="review-label">申请理由</div>
            <div class="review-value reason">{{ request.reason }}</div>
          </div>
        </div>

        <div class="step-actions">
          <button @click="prevStep" class="btn btn-secondary">上一步</button>
          <button @click="submitRequest" class="btn btn-primary" :disabled="submitting">
            {{ submitting ? '提交中...' : '提交申请' }}
          </button>
        </div>
      </div>

      <!-- 提交成功 -->
      <div v-if="submitSuccess" class="success-section">
        <div class="success-icon">✓</div>
        <h2>申请提交成功</h2>
        <p>您的空间申请已提交，请等待管理员审批。</p>
        <p class="success-note">预计审批时间: 1-3 个工作日</p>
        <button @click="goToMySpace" class="btn btn-primary">返回我的空间</button>
      </div>
    </div>
  </LifecycleProvider>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import LifecycleProvider from '@/components/lifecycle/LifecycleProvider.vue'

const router = useRouter()

const currentStep = ref(1)
const submitting = ref(false)
const submitSuccess = ref(false)

const request = ref({
  space_type: '',
  space_name: '',
  quota_gb: 10,
  reason: ''
})

const errors = ref({
  space_name: '',
  reason: ''
})

const quotaRange = ref({
  min: 1 * 1024 * 1024 * 1024,  // 1GB
  max: 100 * 1024 * 1024 * 1024  // 100GB
})

const quotaPresets = [1, 5, 10, 20, 50, 100]

function formatBytes(bytes) {
  if (bytes >= 1024 * 1024 * 1024) {
    return (bytes / (1024 * 1024 * 1024)).toFixed(0) + ' GB'
  }
  return (bytes / (1024 * 1024)).toFixed(0) + ' MB'
}

function validateStep(step) {
  errors.value = { space_name: '', reason: '' }

  if (step === 1) {
    if (!request.value.space_type) {
      return false
    }
  }

  if (step === 2) {
    let valid = true

    if (!request.value.space_name || request.value.space_name.trim() === '') {
      errors.value.space_name = '请输入空间名称'
      valid = false
    } else if (request.value.space_name.length < 2) {
      errors.value.space_name = '空间名称至少2个字符'
      valid = false
    } else if (request.value.space_name.length > 50) {
      errors.value.space_name = '空间名称最多50个字符'
      valid = false
    }

    if (!request.value.reason || request.value.reason.trim() === '') {
      errors.value.reason = '请输入申请理由'
      valid = false
    } else if (request.value.reason.length < 10) {
      errors.value.reason = '申请理由至少10个字符'
      valid = false
    }

    return valid
  }

  return true
}

function nextStep() {
  if (validateStep(currentStep.value)) {
    currentStep.value++
  }
}

function prevStep() {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

async function submitRequest() {
  if (!validateStep(currentStep.value)) return

  submitting.value = true
  try {
    // API call to submit request
    await new Promise(resolve => setTimeout(resolve, 1000))
    submitSuccess.value = true
  } finally {
    submitting.value = false
  }
}

function goToMySpace() {
  router.push('/user/my-space')
}

onMounted(() => {
  // Load user quota limits based on role
})
</script>

<style scoped>
.space-request {
  padding: 20px;
  background: var(--bg-primary, #0d1117);
  min-height: 100vh;
}

.page-header {
  margin-bottom: 32px;
}

.page-header h1 {
  font-size: 24px;
  color: var(--text-primary, #e6edf3);
  margin: 0;
}

.request-content {
  max-width: 700px;
  margin: 0 auto;
}

.steps-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 40px;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.step-number {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--bg-tertiary, #21262d);
  color: var(--text-secondary, #8b949e);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  transition: all 0.3s;
}

.step.active .step-number {
  background: #238636;
  color: white;
}

.step.completed .step-number {
  background: #238636;
  color: white;
}

.step-label {
  font-size: 14px;
  color: var(--text-secondary, #8b949e);
}

.step.active .step-label {
  color: var(--text-primary, #e6edf3);
}

.step-line {
  width: 100px;
  height: 2px;
  background: var(--border, #30363d);
  margin: 0 16px;
}

.step-content {
  background: var(--bg-secondary, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 8px;
  padding: 32px;
}

.step-content h2 {
  font-size: 18px;
  color: var(--text-primary, #e6edf3);
  margin: 0 0 24px 0;
}

.space-type-options {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.type-card {
  position: relative;
  background: var(--bg-tertiary, #21262d);
  border: 2px solid var(--border, #30363d);
  border-radius: 8px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.2s;
}

.type-card:hover {
  border-color: #8b949e;
}

.type-card.selected {
  border-color: #238636;
  background: rgba(35, 134, 54, 0.1);
}

.type-card input {
  position: absolute;
  opacity: 0;
}

.type-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.type-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #e6edf3);
  margin-bottom: 8px;
}

.type-desc {
  font-size: 14px;
  color: var(--text-secondary, #8b949e);
  margin-bottom: 12px;
}

.type-features {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.feature {
  background: var(--bg-secondary, #161b22);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: var(--text-secondary, #8b949e);
}

.form-section {
  margin-bottom: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 14px;
  color: var(--text-secondary, #8b949e);
  margin-bottom: 8px;
}

.required {
  color: #da3633;
}

.form-group input[type="text"],
.form-group textarea {
  width: 100%;
  padding: 12px;
  background: var(--bg-tertiary, #21262d);
  border: 1px solid var(--border, #30363d);
  border-radius: 6px;
  color: var(--text-primary, #e6edf3);
  font-size: 14px;
}

.form-group input.error,
.form-group textarea.error {
  border-color: #da3633;
}

.error-text {
  display: block;
  font-size: 12px;
  color: #da3633;
  margin-top: 4px;
}

.quota-selector {
  background: var(--bg-tertiary, #21262d);
  border-radius: 8px;
  padding: 16px;
}

.quota-range {
  font-size: 12px;
  color: var(--text-secondary, #8b949e);
  margin-bottom: 12px;
}

.quota-selector input[type="range"] {
  width: 100%;
  margin-bottom: 12px;
}

.quota-value {
  display: flex;
  align-items: center;
  gap: 8px;
}

.quota-value input {
  width: 100px;
  padding: 8px;
  background: var(--bg-secondary, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 4px;
  color: var(--text-primary, #e6edf3);
  text-align: center;
}

.quota-value span {
  color: var(--text-secondary, #8b949e);
}

.quota-presets {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.preset-btn {
  padding: 6px 12px;
  background: var(--bg-secondary, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 4px;
  color: var(--text-secondary, #8b949e);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.preset-btn:hover {
  border-color: #238636;
  color: var(--text-primary, #e6edf3);
}

.preset-btn.selected {
  background: #238636;
  border-color: #238636;
  color: white;
}

.step-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.review-section {
  background: var(--bg-tertiary, #21262d);
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
}

.review-item {
  padding: 12px 0;
  border-bottom: 1px solid var(--border, #30363d);
}

.review-item:last-child {
  border-bottom: none;
}

.review-label {
  font-size: 12px;
  color: var(--text-secondary, #8b949e);
  margin-bottom: 4px;
}

.review-value {
  font-size: 16px;
  color: var(--text-primary, #e6edf3);
}

.review-value.reason {
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.success-section {
  text-align: center;
  padding: 48px;
  background: var(--bg-secondary, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 8px;
}

.success-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #238636;
  color: white;
  font-size: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 24px;
}

.success-section h2 {
  font-size: 20px;
  color: var(--text-primary, #e6edf3);
  margin: 0 0 12px 0;
}

.success-section p {
  color: var(--text-secondary, #8b949e);
  margin: 0 0 8px 0;
}

.success-note {
  font-size: 14px;
  margin-bottom: 24px;
}

.btn {
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  border: none;
  font-size: 14px;
}

.btn-primary {
  background: #238636;
  color: white;
}

.btn-primary:disabled {
  background: #21262d;
  color: #484f58;
}

.btn-secondary {
  background: var(--bg-secondary, #161b22);
  color: var(--text-primary, #e6edf3);
  border: 1px solid var(--border, #30363d);
}
</style>
