<template>
  <LifecycleProvider>
  <div class="space-request">
    <header class="space-request__header">
      <h1 class="space-request__title">申请新空间</h1>
    </header>

    <div class="space-request__content">
      <!-- 步骤指示器 -->
      <div class="steps-indicator">
        <div :class="['step', { 'step--active': currentStep >= 1, 'step--completed': currentStep > 1 }]">
          <div class="step__number">1</div>
          <div class="step__label">选择类型</div>
        </div>
        <div class="step__line"></div>
        <div :class="['step', { 'step--active': currentStep >= 2, 'step--completed': currentStep > 2 }]">
          <div class="step__number">2</div>
          <div class="step__label">填写信息</div>
        </div>
        <div class="step__line"></div>
        <div :class="['step', { 'step--active': currentStep >= 3 }]">
          <div class="step__number">3</div>
          <div class="step__label">提交申请</div>
        </div>
      </div>

      <!-- 步骤1: 选择空间类型 -->
      <div v-show="currentStep === 1" class="step-content">
        <h2 class="step-content__title">选择空间类型</h2>
        <div class="type-options">
          <label :class="['type-card', { 'type-card--selected': request.space_type === 'team' }]">
            <input v-model="request.space_type" type="radio" value="team" class="type-card__input" />
            <div class="type-card__icon">👔</div>
            <div class="type-card__name">团队空间</div>
            <div class="type-card__desc">适用于多人协作，可分配配额给团队成员</div>
            <div class="type-card__features">
              <span class="feature-tag">多成员协作</span>
              <span class="feature-tag">配额管理</span>
              <span class="feature-tag">权限控制</span>
            </div>
          </label>

          <label :class="['type-card', { 'type-card--selected': request.space_type === 'personal' }]">
            <input v-model="request.space_type" type="radio" value="personal" class="type-card__input" />
            <div class="type-card__icon">👤</div>
            <div class="type-card__name">私人空间</div>
            <div class="type-card__desc">仅自己使用，适合个人文件存储</div>
            <div class="type-card__features">
              <span class="feature-tag">专属配额</span>
              <span class="feature-tag">独立使用</span>
              <span class="feature-tag">简单管理</span>
            </div>
          </label>
        </div>

        <div class="step-actions">
          <button @click="nextStep" class="button-primary" :disabled="!request.space_type">
            下一步
          </button>
        </div>
      </div>

      <!-- 步骤2: 填写信息 -->
      <div v-show="currentStep === 2" class="step-content">
        <h2 class="step-content__title">填写申请信息</h2>

        <div class="form-section">
          <div class="form-group">
            <label class="form-label">空间名称 <span class="required">*</span></label>
            <input
              v-model="request.space_name"
              type="text"
              placeholder="输入空间名称"
              :class="['form-input', { 'form-input--error': errors.space_name }]"
            />
            <span v-if="errors.space_name" class="form-error">{{ errors.space_name }}</span>
          </div>

          <div class="form-group">
            <label class="form-label">申请配额 <span class="required">*</span></label>
            <div class="quota-selector">
              <div class="quota-range">
                可申请: {{ formatBytes(quotaRange.min) }} - {{ formatBytes(quotaRange.max) }}
              </div>
              <input
                v-model.number="request.quota_gb"
                type="range"
                class="quota-slider"
                :min="quotaRange.min / (1024 * 1024 * 1024)"
                :max="quotaRange.max / (1024 * 1024 * 1024)"
                step="1"
              />
              <div class="quota-value">
                <input
                  v-model.number="request.quota_gb"
                  type="number"
                  class="form-input form-input--inline"
                  :min="quotaRange.min / (1024 * 1024 * 1024)"
                  :max="quotaRange.max / (1024 * 1024 * 1024)"
                />
                <span class="quota-unit">GB</span>
              </div>
            </div>
            <div class="quota-presets">
              <button
                v-for="preset in quotaPresets"
                :key="preset"
                :class="['preset-btn', { 'preset-btn--selected': request.quota_gb === preset }]"
                @click="request.quota_gb = preset"
              >
                {{ preset }} GB
              </button>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">申请理由 <span class="required">*</span></label>
            <textarea
              v-model="request.reason"
              placeholder="请详细说明申请空间的原因和用途..."
              rows="5"
              :class="['form-textarea', { 'form-textarea--error': errors.reason }]"
            ></textarea>
            <span v-if="errors.reason" class="form-error">{{ errors.reason }}</span>
          </div>
        </div>

        <div class="step-actions">
          <button @click="prevStep" class="button-secondary">上一步</button>
          <button @click="nextStep" class="button-primary">下一步</button>
        </div>
      </div>

      <!-- 步骤3: 确认提交 -->
      <div v-show="currentStep === 3" class="step-content">
        <h2 class="step-content__title">确认申请信息</h2>

        <div class="review-section">
          <div class="review-item">
            <div class="review-item__label">空间类型</div>
            <div class="review-item__value">{{ request.space_type === 'team' ? '团队空间' : '私人空间' }}</div>
          </div>
          <div class="review-item">
            <div class="review-item__label">空间名称</div>
            <div class="review-item__value">{{ request.space_name }}</div>
          </div>
          <div class="review-item">
            <div class="review-item__label">申请配额</div>
            <div class="review-item__value">{{ request.quota_gb }} GB</div>
          </div>
          <div class="review-item">
            <div class="review-item__label">申请理由</div>
            <div class="review-item__value review-item__value--reason">{{ request.reason }}</div>
          </div>
        </div>

        <div class="step-actions">
          <button @click="prevStep" class="button-secondary">上一步</button>
          <button @click="submitRequest" class="button-primary" :disabled="submitting">
            {{ submitting ? '提交中...' : '提交申请' }}
          </button>
        </div>
      </div>

      <!-- 提交成功 -->
      <div v-if="submitSuccess" class="success-section">
        <div class="success-section__icon">✓</div>
        <h2 class="success-section__title">申请提交成功</h2>
        <p class="success-section__message">您的空间申请已提交，请等待管理员审批。</p>
        <p class="success-section__note">预计审批时间: 1-3 个工作日</p>
        <button @click="goToMySpace" class="button-primary">返回我的空间</button>
      </div>
    </div>
  </LifecycleProvider>
</template>

<script setup>
import { ref, onMounted } from 'vue'
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
  min: 1 * 1024 * 1024 * 1024,
  max: 100 * 1024 * 1024 * 1024
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
    if (!request.value.space_type) return false
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
  if (currentStep.value > 1) currentStep.value--
}

async function submitRequest() {
  if (!validateStep(currentStep.value)) return

  submitting.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    submitSuccess.value = true
  } finally {
    submitting.value = false
  }
}

function goToMySpace() {
  router.push('/user/my-space')
}

onMounted(() => {})
</script>

<style scoped>
/* === SpaceRequest - 申请新空间页面 === */

.space-request {
  padding: var(--spacing-lg);
  max-width: 800px;
  margin: 0 auto;
}

/* === Header === */
.space-request__header {
  margin-bottom: var(--spacing-xl);
}

.space-request__title {
  font: var(--text-display-md);
  color: var(--color-ink);
  margin: 0;
}

/* === Content === */
.space-request__content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

/* === Steps Indicator === */
.steps-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg) 0;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xxs);
}

.step__number {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  background: var(--color-canvas-parchment);
  color: var(--color-ink-muted-48);
  display: flex;
  align-items: center;
  justify-content: center;
  font: var(--text-caption-strong);
  transition: background 0.2s, color 0.2s;
}

.step--active .step__number {
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.step--completed .step__number {
  background: var(--color-success);
  color: var(--color-on-primary);
}

.step__label {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.step--active .step__label {
  color: var(--color-ink);
}

.step__line {
  flex: 1;
  height: 2px;
  background: var(--color-hairline);
  max-width: 60px;
}

/* === Step Content === */
.step-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.step-content__title {
  font: var(--text-body-strong);
  color: var(--color-ink);
  margin: 0;
}

/* === Type Options === */
.type-options {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-md);
}

.type-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg);
  background: var(--color-canvas);
  border: 2px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}

.type-card:hover {
  border-color: var(--color-primary);
}

.type-card--selected {
  border-color: var(--color-primary);
  background: var(--color-primary-faint);
}

.type-card__input {
  display: none;
}

.type-card__icon {
  font-size: 48px;
}

.type-card__name {
  font: var(--text-body-strong);
  color: var(--color-ink);
}

.type-card__desc {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
  text-align: center;
}

.type-card__features {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xxs);
  justify-content: center;
}

.feature-tag {
  padding: var(--spacing-xxs) var(--spacing-sm);
  background: var(--color-canvas-parchment);
  border-radius: var(--radius-pill);
  font: var(--text-fine-print);
  color: var(--color-ink-muted-48);
}

/* === Form Section === */
.form-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xxs);
}

.form-label {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.required {
  color: var(--color-danger);
}

.form-input {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  font: var(--text-body);
  color: var(--color-ink);
  box-sizing: border-box;
}

.form-input:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

.form-input--error {
  border-color: var(--color-danger);
}

.form-input--inline {
  width: 80px;
  text-align: center;
}

.form-textarea {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-canvas);
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

.form-textarea--error {
  border-color: var(--color-danger);
}

.form-error {
  font: var(--text-caption);
  color: var(--color-danger);
}

/* === Quota Selector === */
.quota-selector {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.quota-range {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.quota-slider {
  width: 100%;
  height: 8px;
  border-radius: var(--radius-full);
  background: var(--color-canvas-parchment);
  appearance: none;
  cursor: pointer;
}

.quota-slider::-webkit-slider-thumb {
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  cursor: pointer;
}

.quota-value {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.quota-unit {
  font: var(--text-body);
  color: var(--color-ink-muted-48);
}

.quota-presets {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.preset-btn {
  padding: var(--spacing-xxs) var(--spacing-sm);
  background: var(--color-canvas-parchment);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  font: var(--text-caption);
  color: var(--color-ink);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.preset-btn:hover {
  background: var(--color-canvas);
}

.preset-btn--selected {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-on-primary);
}

/* === Review Section === */
.review-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
}

.review-item {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-md);
}

.review-item__label {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.review-item__value {
  font: var(--text-body);
  color: var(--color-ink);
  text-align: right;
}

.review-item__value--reason {
  max-width: 300px;
  text-align: right;
}

/* === Step Actions === */
.step-actions {
  display: flex;
  gap: var(--spacing-sm);
  justify-content: flex-end;
}

/* === Success Section === */
.success-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-xxl);
  text-align: center;
}

.success-section__icon {
  width: 64px;
  height: 64px;
  border-radius: var(--radius-full);
  background: var(--color-success);
  color: var(--color-on-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
}

.success-section__title {
  font: var(--text-body-strong);
  color: var(--color-ink);
  margin: 0;
}

.success-section__message {
  font: var(--text-body);
  color: var(--color-ink-muted-48);
  margin: 0;
}

.success-section__note {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
  margin: 0;
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
</style>