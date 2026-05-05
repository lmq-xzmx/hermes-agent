<template>
  <div class="login-view">
    <!-- Login Screen -->
    <div v-if="mode === 'login'" class="login-container">
      <TileLight class="login-tile">
        <div class="login-box">
          <div class="login-header">
            <div class="brand-icon">🚀</div>
            <h1 class="login-title">Hermes 文件管理器</h1>
            <p class="login-subtitle">登录以访问您的文件</p>
          </div>

          <div v-if="error" class="error-msg">
            <span class="error-icon">⚠️</span>
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
                  <span class="toggle-icon">{{ showPassword ? '🙈' : '👁' }}</span>
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
            <div class="brand-icon">🚀</div>
            <h1 class="login-title">创建账户</h1>
            <p class="login-subtitle">注册以开始管理文件</p>
          </div>

          <div v-if="error" class="error-msg">
            <span class="error-icon">⚠️</span>
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
                  <span class="toggle-icon">{{ showPassword ? '🙈' : '👁' }}</span>
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
import { TileLight } from '../components/common'

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
.login-view {
  width: 100%;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-canvas-parchment);
}

.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: var(--space-lg);
  width: 100%;
}

.login-tile {
  width: 100%;
  max-width: 400px;
}

.login-box {
  width: 100%;
  padding: var(--space-lg);
}

.login-header {
  text-align: center;
  margin-bottom: var(--space-xl);
}

.brand-icon {
  font-size: 56px;
  margin-bottom: var(--space-md);
  display: block;
}

.login-title {
  font-family: var(--font-family-display);
  font-size: 34px;
  font-weight: 600;
  line-height: 1.47;
  letter-spacing: -0.374px;
  color: var(--color-ink);
  margin: 0 0 var(--space-xs);
}

.login-subtitle {
  font: var(--font-family-text);
  color: var(--color-ink-muted-48);
  margin: 0;
}

.error-msg {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  background: rgba(255, 59, 48, 0.08);
  border: 1px solid var(--color-danger);
  border-radius: var(--radius-md);
  padding: var(--space-sm) var(--space-md);
  margin-bottom: var(--space-lg);
  color: var(--color-danger);
  font: var(--font-family-text);
}

.error-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.login-form {
  margin-bottom: var(--space-lg);
}

.form-field {
  margin-bottom: var(--space-md);
}

.form-label {
  display: block;
  font: var(--font-family-text);
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: var(--space-xxs);
}

/* Apple Input - pill shape */
.apple-input {
  padding: 12px 17px;
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  color: var(--color-ink);
  font: var(--font-family-text);
  transition: border-color 0.2s;
  height: 44px;
  box-sizing: border-box;
  width: 100%;
}

.apple-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.15);
}

.apple-input.full-width {
  width: 100%;
}

.password-wrapper {
  position: relative;
}

.password-wrapper .apple-input {
  padding-right: 48px;
}

/* Password Toggle - Apple Icon Button */
.password-toggle {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: none;
  cursor: pointer;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-full);
  transition: background-color 0.15s ease;
}

.password-toggle:hover {
  background: rgba(0, 0, 0, 0.05);
}

.password-toggle:active {
  transform: translateY(-50%) scale(0.95);
}

.password-toggle.active {
  background: rgba(0, 0, 0, 0.05);
}

.toggle-icon {
  font-size: 18px;
  line-height: 1;
}

.checkbox-field {
  margin-bottom: var(--space-lg);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  cursor: pointer;
  font: var(--font-family-text);
  color: var(--color-ink-muted-80);
  user-select: none;
}

.checkbox-input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.checkbox-custom {
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-hairline);
  border-radius: var(--radius-xs);
  background: var(--color-canvas);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.checkbox-input:checked + .checkbox-custom {
  background: var(--color-primary);
  border-color: var(--color-primary);
}

.checkbox-input:checked + .checkbox-custom::after {
  content: '✓';
  color: white;
  font-size: 12px;
  font-weight: 600;
}

.checkbox-input:focus + .checkbox-custom {
  box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.15);
}

.checkbox-input:hover + .checkbox-custom {
  border-color: var(--color-primary);
}

.checkbox-text {
  flex: 1;
}

/* Button Full Width - utility */
.btn-full {
  width: 100%;
}

.login-footer {
  text-align: center;
  font: var(--font-family-text);
  color: var(--color-ink-muted-48);
  margin: 0;
}

.text-link {
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 600;
}

.text-link:hover {
  text-decoration: underline;
}
</style>
