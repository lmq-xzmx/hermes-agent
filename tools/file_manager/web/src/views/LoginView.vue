<template>
  <div class="login-view">
    <!-- Login Screen -->
    <div v-if="mode === 'login'" class="login-container">
      <TileLight class="login-tile">
        <div class="login-box">
          <div class="login-header">
            <Icon name="rocket" :size="48" class="brand-icon" />
            <h1 class="login-title">Hermes 文件管理器</h1>
            <p class="login-subtitle">登录以访问您的文件</p>
          </div>

          <div v-if="error" class="error-msg">
            <Icon name="warning" :size="16" class="error-icon" />
            {{ error }}
          </div>

          <form @submit.prevent="handleLogin" class="login-form">
            <div class="form-field">
              <label for="username" class="form-label">用户名</label>
              <input
                type="text"
                id="username"
                v-model="loginForm.username"
                required
                autocomplete="username"
                class="apple-input full-width"
              >
            </div>

            <div class="form-field">
              <label for="password" class="form-label">密码</label>
              <div class="password-wrapper">
                <input
                  :type="showPassword ? 'text' : 'password'"
                  id="password"
                  v-model="loginForm.password"
                  required
                  autocomplete="current-password"
                  class="apple-input full-width"
                >
                <button
                  type="button"
                  class="password-toggle"
                  :class="{ active: showPassword }"
                  @click="showPassword = !showPassword"
                  :aria-label="showPassword ? '隐藏密码' : '显示密码'"
                >
                  <Icon :name="showPassword ? 'eye-off' : 'eye'" :size="16" class="toggle-icon" />
                </button>
              </div>
            </div>

            <div class="form-field checkbox-field">
              <label class="checkbox-label">
                <input
                  type="checkbox"
                  v-model="loginForm.rememberMe"
                  class="checkbox-input"
                >
                <span class="checkbox-custom"></span>
                <span class="checkbox-text">记住账号密码</span>
              </label>
            </div>

            <button type="submit" class="btn-apple-primary btn-full">登录</button>
          </form>

          <p class="login-footer">
            没有账户？
            <a href="#" @click.prevent="mode = 'register'" class="text-link">立即注册</a>
          </p>
        </div>
      </TileLight>
    </div>

    <!-- Register Screen -->
    <div v-else class="login-container">
      <TileLight class="login-tile">
        <div class="login-box">
          <div class="login-header">
            <Icon name="rocket" :size="48" class="brand-icon" />
            <h1 class="login-title">创建账户</h1>
            <p class="login-subtitle">注册以开始管理文件</p>
          </div>

          <div v-if="error" class="error-msg">
            <Icon name="warning" :size="16" class="error-icon" />
            {{ error }}
          </div>

          <form @submit.prevent="handleRegister" class="login-form">
            <div class="form-field">
              <label for="regUsername" class="form-label">用户名</label>
              <input
                type="text"
                id="regUsername"
                v-model="registerForm.username"
                required
                autocomplete="username"
                minlength="3"
                maxlength="32"
                class="apple-input full-width"
              >
            </div>

            <div class="form-field">
              <label for="regPassword" class="form-label">密码</label>
              <div class="password-wrapper">
                <input
                  :type="showPassword ? 'text' : 'password'"
                  id="regPassword"
                  v-model="registerForm.password"
                  required
                  autocomplete="new-password"
                  minlength="6"
                  class="apple-input full-width"
                >
                <button
                  type="button"
                  class="password-toggle"
                  :class="{ active: showPassword }"
                  @click="showPassword = !showPassword"
                  :aria-label="showPassword ? '隐藏密码' : '显示密码'"
                >
                  <Icon :name="showPassword ? 'eye-off' : 'eye'" :size="16" class="toggle-icon" />
                </button>
              </div>
            </div>

            <div class="form-field">
              <label for="regPassword2" class="form-label">确认密码</label>
              <div class="password-wrapper">
                <input
                  :type="showPassword ? 'text' : 'password'"
                  id="regPassword2"
                  v-model="registerForm.password2"
                  required
                  autocomplete="new-password"
                  class="apple-input full-width"
                >
              </div>
            </div>

            <button type="submit" class="btn-apple-primary btn-full">创建账户</button>
          </form>

          <p class="login-footer">
            已有账户？
            <a href="#" @click.prevent="mode = 'login'" class="text-link">立即登录</a>
          </p>
        </div>
      </TileLight>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/authStore'
import { TileLight, Icon } from '../components/common'

const emit = defineEmits(['login-success'])
const router = useRouter()
const authStore = useAuthStore()

const mode = ref('login')
const error = ref('')
const showPassword = ref(false)

const loginForm = ref({
  username: '',
  password: '',
  rememberMe: false
})

const registerForm = ref({
  username: '',
  password: '',
  password2: ''
})

onMounted(async () => {
  const savedRemember = localStorage.getItem('hfm_remember')
  if (savedRemember === 'true') {
    loginForm.value.username = localStorage.getItem('hfm_username') || ''
    loginForm.value.password = localStorage.getItem('hfm_password') || ''
    loginForm.value.rememberMe = true
  }

  const token = localStorage.getItem('hfm_token')
  if (token) {
    try {
      await authStore.fetchCurrentUser()
      router.push('/files')
    } catch (e) {
      localStorage.removeItem('hfm_token')
    }
  }
})

async function handleLogin() {
  error.value = ''

  try {
    await authStore.login(loginForm.value.username, loginForm.value.password)

    if (loginForm.value.rememberMe) {
      localStorage.setItem('hfm_remember', 'true')
      localStorage.setItem('hfm_username', loginForm.value.username)
      localStorage.setItem('hfm_password', loginForm.value.password)
    } else {
      localStorage.removeItem('hfm_remember')
      localStorage.removeItem('hfm_username')
      localStorage.removeItem('hfm_password')
    }

    emit('login-success', {
      token: authStore.token,
      username: authStore.username
    })
    router.push('/files')
  } catch (err) {
    error.value = err.message
  }
}

async function handleRegister() {
  error.value = ''

  if (!registerForm.value.username || !registerForm.value.password) {
    error.value = '请填写所有字段'
    return
  }

  if (registerForm.value.username.length < 3) {
    error.value = '用户名至少需要3个字符'
    return
  }

  if (registerForm.value.password.length < 6) {
    error.value = '密码至少需要6个字符'
    return
  }

  if (registerForm.value.password !== registerForm.value.password2) {
    error.value = '两次密码输入不一致'
    return
  }

  try {
    await authStore.register(registerForm.value.username, registerForm.value.password)
    emit('login-success', {
      token: authStore.token,
      username: authStore.username
    })
    router.push('/files')
  } catch (err) {
    error.value = err.message
  }
}
</script>

<style scoped>
/* ============================================
   Block: login-view
   Login View - Apple DESIGN.md Compliant
   ============================================ */

/* === Layout === */
.login-view {
  /* Layout */
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;

  /* Visual */
  background: transparent;
  padding: var(--spacing-lg);
}

/* === Container === */
.login-container {
  /* Layout */
  display: flex;
  align-items: center;
  justify-content: center;

  /* Box Model */
  width: 100%;
  max-width: 420px;
}

/* === Tile === */
.login-tile {
  /* Box Model */
  padding: var(--spacing-xl);
  width: 100%;

  /* Visual - 确保白色背景和边框 */
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
}

/* === Box === */
.login-box {
  /* Layout */
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

/* === Header === */
.login-header {
  /* Layout */
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;

  /* Box Model */
  margin-bottom: var(--spacing-md);
}

.brand-icon {
  /* Layout */
  margin-bottom: var(--spacing-md);
}

.login-title {
  /* Typography */
  font: var(--text-tagline);
  color: var(--color-ink);

  /* Reset */
  margin: 0 0 var(--spacing-xs);
}

.login-subtitle {
  /* Typography */
  font: var(--text-body);
  color: var(--color-secondary);

  /* Reset */
  margin: 0;
}

/* === Error Message === */
.error-msg {
  /* Layout */
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);

  /* Visual */
  background: var(--color-danger-subtle);
  color: var(--color-danger);

  /* Box Model */
  padding: var(--spacing-sm) var(--spacing-md);

  /* Shape */
  border-radius: var(--radius-md);
}

.error-icon {
  /* Typography */
  font-size: 16px;
}

/* === Form === */
.login-form {
  /* Layout */
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.form-field {
  /* Layout */
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xxs);
}

.form-label {
  /* Typography */
  font: var(--text-caption-strong);
  color: var(--color-ink);
}

/* === Apple Input === */
.apple-input {
  /* Box Model */
  padding: var(--spacing-sm);

  /* Visual */
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);

  /* Typography */
  font: var(--text-body);
  color: var(--color-ink);
  box-sizing: border-box;

  /* Interaction */
  transition: border-color 0.2s ease;
}

.apple-input:focus {
  /* Outline */
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
  border-color: transparent;
}

.apple-input::placeholder {
  /* Typography */
  color: var(--color-secondary);
}

.full-width {
  /* Box Model */
  width: 100%;
  box-sizing: border-box;
}

/* === Password Wrapper === */
.password-wrapper {
  /* Positioning */
  position: relative;
}

.password-wrapper .apple-input {
  /* Box Model */
  padding-right: 44px;
}

.password-toggle {
  /* Positioning */
  position: absolute;
  right: var(--spacing-sm);
  top: 50%;
  transform: translateY(-50%);

  /* Visual */
  background: transparent;
  border: none;

  /* Layout */
  display: flex;
  align-items: center;
  justify-content: center;

  /* Box Model */
  width: 28px;
  height: 28px;

  /* Interaction */
  cursor: pointer;
  opacity: 0.6;
  transition: opacity 0.15s ease;
}

.password-toggle:hover,
.password-toggle.active {
  opacity: 1;
}

.toggle-icon {
  /* Typography */
  font-size: 16px;
}

/* === Checkbox === */
.checkbox-field {
  /* Layout */
  flex-direction: row;
  align-items: center;
}

.checkbox-label {
  /* Layout */
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);

  /* Interaction */
  cursor: pointer;
}

.checkbox-input {
  /* Positioning */
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.checkbox-custom {
  /* Visual */
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);

  /* Shape */
  border-radius: var(--radius-xs);

  /* Box Model */
  width: 20px;
  height: 20px;

  /* Layout */
  display: flex;
  align-items: center;
  justify-content: center;

  /* Interaction */
  transition: background-color 0.15s ease, border-color 0.15s ease;
}

.checkbox-input:checked + .checkbox-custom {
  /* Visual */
  background: var(--color-primary);
  border-color: var(--color-primary);
}

.checkbox-input:checked + .checkbox-custom::after {
  /* Content */
  content: '✓';

  /* Typography */
  font-size: 12px;
  font-weight: 600;
  color: var(--color-body-on-dark);
}

.checkbox-input:focus + .checkbox-custom {
  /* Outline */
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

.checkbox-text {
  /* Typography */
  font: var(--text-body);
  color: var(--color-ink);
}

/* === Buttons === */
.btn-apple-primary {
  /* Layout */
  display: inline-flex;
  align-items: center;
  justify-content: center;

  /* Box Model */
  padding: 11px 22px;
  min-height: 44px;

  /* Typography */
  font: var(--text-body);
  font-weight: 500;
  color: var(--color-body-on-dark);

  /* Shape */
  border-radius: var(--radius-pill);
  border: none;

  /* Visual */
  background: var(--color-primary);

  /* Interaction */
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.1s ease;
}

.btn-apple-primary:hover {
  /* Visual */
  background: var(--color-primary-hover);
}

.btn-apple-primary:active {
  /* Interaction */
  transform: scale(0.97);
}

.btn-apple-primary:focus {
  /* Outline */
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

.btn-full {
  /* Box Model */
  width: 100%;
}

/* === Footer === */
.login-footer {
  /* Typography */
  font: var(--text-body);
  color: var(--color-secondary);

  /* Layout */
  text-align: center;

  /* Reset */
  margin: var(--spacing-md) 0 0;
}

.text-link {
  /* Typography */
  font: var(--text-body);
  color: var(--color-primary);

  /* Interaction */
  text-decoration: none;
  transition: color 0.15s ease;
}

.text-link:hover {
  /* Visual */
  color: var(--color-primary-hover);
  text-decoration: underline;
}
</style>
