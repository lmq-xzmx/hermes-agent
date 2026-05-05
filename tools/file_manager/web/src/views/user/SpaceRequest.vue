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
          <button @click="nextStep" class="btn-apple-primary" :disabled="!request.space_type">
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
          <button @click="prevStep" class="btn-apple-secondary">上一步</button>
          <button @click="nextStep" class="btn-apple-primary">下一步</button>
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
          <button @click="prevStep" class="btn-apple-secondary">上一步</button>
          <button @click="submitRequest" class="btn-apple-primary" :disabled="submitting">
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
        <button @click="goToMySpace" class="btn-apple-primary">返回我的空间</button>
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
  background: var(--bg-primary);
  min-height: 100vh;
}

.page-header {
  margin-bottom: 32px;
}

.page-header h1 {
  font-size: 24px;
  color: var(--text-primary);
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
  border-radius: var(--radius-full);
  background: var(--color-surface-tile-3);
  color: var(--color-ink-muted-48);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  transition: all 0.3s;
}

.step.active .step-number {
  background: var(--color-success);
  color: white;
}

.step.completed .step-number {
  background: var(--color-success);
  color: white;
}

.step-label {
  font-size: 14px;
  color: var(--color-ink-muted-48);
}

.step.active .step-label {
  color: var(--text-primary);
}

.step-line {
  width: 100px;
  height: 2px;
  background: var(--color-hairline);
  margin: 0 16px;
}

.step-content {
  background: var(--color-surface-tile-1);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  padding: 32px;
}

.step-content h2 {
  font-size: 18px;
  color: var(--text-primary);
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
  background: var(--color-surface-tile-3);
  border: 2px solid var(--color-hairline);
  border-radius: var(--radius-md);
  padding: 24px;
  cursor: pointer;
  transition: all 0.2s;
}

.type-card:hover {
  border-color: var(--color-ink-muted-48);
}

.type-card.selected {
  border-color: var(--color-success);
  background: var(--color-success-subtle);
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
  color: var(--text-primary);
  margin-bottom: 8px;
}

.type-desc {
  font-size: 14px;
  color: var(--color-ink-muted-48);
  margin-bottom: 12px;
}

.type-features {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.feature {
  background: var(--color-surface-tile-1);
  padding: 4px 8px;
  border-radius: var(--radius-md);
  font-size: 12px;
  color: var(--color-ink-muted-48);
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
  color: var(--color-ink-muted-48);
  margin-bottom: 8px;
}

.required {
  color: var(--color-danger);
}

.form-group input[type="text"],
.form-group textarea {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  color: var(--color-ink);
  font: var(--text-body);
  font-size: 17px;
  line-height: 1.47;
  letter-spacing: -0.374px;
  transition: border-color 0.2s ease;
}

.form-group input[type="text"]:focus,
.form-group textarea:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 0;
}

.form-group input.error,
.form-group textarea.error {
  border-color: var(--color-danger);
}

.error-text {
  display: block;
  font-family: var(--font-family-text);
  font-size: 12px;
  color: var(--color-danger);
  margin-top: 4px;
}

.quota-selector {
  background: var(--color-canvas-parchment);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
}

.quota-range {
  font-family: var(--font-family-text);
  font-size: 12px;
  color: var(--color-ink-muted-48);
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
  padding: 10px;
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  color: var(--color-ink);
  font-family: var(--font-family-text);
  font-size: 17px;
  text-align: center;
}

.quota-value span {
  color: var(--color-ink-muted-48);
}

.quota-presets {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-top: 12px;
}

.preset-btn {
  padding: 8px 16px;
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  color: var(--color-ink-muted-48);
  font-family: var(--font-family-text);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.preset-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.preset-btn.selected {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-on-primary);
}

.step-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.review-section {
  background: var(--color-canvas-parchment);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  margin-bottom: var(--space-lg);
}

.review-item {
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid var(--color-divider-soft);
}

.review-item:last-child {
  border-bottom: none;
}

.review-label {
  font-family: var(--font-family-text);
  font-size: 12px;
  color: var(--color-ink-muted-48);
  margin-bottom: 4px;
}

.review-value {
  font-family: var(--font-family-text);
  font-size: 16px;
  color: var(--color-ink);
}

.review-value.reason {
  font-family: var(--font-family-text);
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.success-section {
  text-align: center;
  padding: 48px;
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
}

.success-icon {
  width: 64px;
  height: 64px;
  border-radius: var(--radius-full);
  background: var(--color-success);
  color: white;
  font-size: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 24px;
}

.success-section h2 {
  font-family: var(--font-display);
  font-size: 20px;
  color: var(--color-ink);
  margin: 0 0 12px 0;
}

.success-section p {
  color: var(--color-ink-muted-48);
  margin: 0 0 8px 0;
}

.success-note {
  font-size: 14px;
  margin-bottom: 24px;
}

.btn {
  padding: 11px 22px;
  border-radius: var(--radius-pill);
  cursor: pointer;
  border: none;
  font-family: var(--font-family-text);
  font-size: 17px;
  font-weight: 400;
  line-height: 1.47;
  letter-spacing: -0.374px;
  transition: var(--transition-active);
}

</style>
