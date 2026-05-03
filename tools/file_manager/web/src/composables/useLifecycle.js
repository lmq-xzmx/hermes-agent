/**
 * Vue 3 Composable: 生命周期操作拦截器
 *
 * 在执行危险操作前检查约束条件，
 * 违规时显示引导弹窗而非直接拒绝
 */
import { ref, shallowRef } from 'vue'

export function useLifecycle() {
  const enabled = ref(true)
  const debug = ref(false)
  const constraints = shallowRef(new Map())
  const guidanceCallbacks = shallowRef(new Map())

  // 初始化默认约束
  function registerDefaultConstraints() {
    const c = new Map()

    // 上传文件约束
    c.set('upload_file', {
      check: async (ctx) => ctx.isMember && ctx.hasQuota,
      error: {
        title: '无法上传文件',
        message: '您还没有加入任何团队，无法上传文件。请先加入一个团队或创建一个新团队。',
        icon: '📤'
      },
      guidance: { label: '加入团队', icon: '👥', path: '/teams' }
    })

    // 创建团队约束
    c.set('create_team', {
      check: async (ctx) => ctx.hasAvailablePool,
      error: {
        title: '无法创建团队',
        message: '系统暂无可用存储池，无法创建新团队。请联系管理员创建存储池后再试。',
        icon: '👥'
      },
      guidance: { label: '联系管理员', icon: '📧', action: 'showContactAdminModal' }
    })

    // 创建私人空间约束
    c.set('create_private_space', {
      check: async (ctx) => ctx.isTeamMember,
      error: {
        title: '无法创建私人空间',
        message: '只有团队成员才能申请私人空间。',
        icon: '🔒'
      },
      guidance: { label: '加入团队', icon: '👥', path: '/teams' }
    })

    // 删除存储池约束
    c.set('delete_pool', {
      check: async (ctx) => ctx.teamCount === 0,
      error: {
        title: '无法删除存储池',
        message: '该存储池仍有团队使用，无法删除。请先将团队迁移到其他存储池。',
        icon: '⚠️'
      },
      guidance: { label: '查看团队', icon: '👥', path: '/admin/teams' }
    })

    // 删除空间约束
    c.set('delete_space', {
      check: async (ctx) => ctx.memberCount === 0 && ctx.isOwner,
      error: {
        title: '无法删除空间',
        message: '该空间仍有成员，无法删除。请先移除所有成员。',
        icon: '👥'
      },
      guidance: { label: '查看成员', icon: '👥', path: '/admin/members' }
    })

    // 删除团队约束
    c.set('delete_team', {
      check: async (ctx) => ctx.isOwner,
      error: {
        title: '无法删除团队',
        message: '只有团队所有者可以删除团队。',
        icon: '👥'
      },
      guidance: { label: '联系管理员', icon: '📧', action: 'showContactAdminModal' }
    })

    // 邀请成员约束
    c.set('invite_member', {
      check: async (ctx) => ctx.isOwner,
      error: {
        title: '无法邀请成员',
        message: '只有空间所有者可以邀请新成员。',
        icon: '👥'
      },
      guidance: { label: '联系管理员', icon: '📧', action: 'showContactAdminModal' }
    })

    // 配额检查约束
    c.set('check_quota', {
      check: async (ctx) => ctx.sufficientQuota,
      error: {
        title: '配额不足',
        message: '存储配额已用尽，无法上传新文件。请清理回收站或联系管理员申请扩容。',
        icon: '💾'
      },
      guidance: { label: '查看回收站', icon: '🗑️', path: '/trash' }
    })

    // 更新配额约束
    c.set('update_quota', {
      check: async (ctx) => ctx.isOwner,
      error: {
        title: '无法修改配额',
        message: '只有空间所有者可以修改配额。',
        icon: '💾'
      },
      guidance: { label: '联系管理员', icon: '📧', action: 'showContactAdminModal' }
    })

    // 加入团队约束
    c.set('join_team', {
      check: async (ctx) => ctx.credentialValid,
      error: {
        title: '无法加入团队',
        message: '邀请码已过期或无效。',
        icon: '🔗'
      },
      guidance: { label: '联系管理员', icon: '📧', action: 'showContactAdminModal' }
    })

    constraints.value = c
  }

  registerDefaultConstraints()

  /**
   * 注册约束规则
   */
  function registerConstraint(action, config) {
    const c = new Map(constraints.value)
    c.set(action, config)
    constraints.value = c
  }

  /**
   * 注册引导回调
   */
  function registerGuidanceCallback(action, callback) {
    const c = new Map(guidanceCallbacks.value)
    c.set(action, callback)
    guidanceCallbacks.value = c
  }

  /**
   * 执行操作前的约束检查
   */
  async function beforeAction(action, context) {
    if (!enabled.value) return { allowed: true }

    const constraint = constraints.value.get(action)
    if (!constraint) {
      debug.value && console.log(`[Lifecycle] No constraint for action: ${action}`)
      return { allowed: true }
    }

    try {
      const passed = await constraint.check(context)

      if (passed) {
        debug.value && console.log(`[Lifecycle] Constraint passed: ${action}`)
        return { allowed: true }
      }

      debug.value && console.log(`[Lifecycle] Constraint violated: ${action}`)
      return {
        allowed: false,
        error: constraint.error,
        guidance: constraint.guidance
      }
    } catch (e) {
      console.error(`[Lifecycle] Error checking constraint: ${action}`, e)
      return { allowed: true, error: e.message }
    }
  }

  /**
   * 显示引导弹窗
   */
  function showGuidanceModal(config) {
    const modal = new GuidanceModal({
      title: config.error.title,
      message: config.error.message,
      icon: config.error.icon,
      guidance: config.guidance,
      onAction: () => executeGuidance(config.guidance),
      onDismiss: () => onGuidanceDismissed(config)
    })
    modal.show()
    return modal
  }

  /**
   * 执行引导操作
   */
  function executeGuidance(guidance) {
    if (guidance.path) {
      window.location.hash = guidance.path
    } else if (guidance.action) {
      const callback = guidanceCallbacks.value.get(guidance.action)
      if (callback) callback()
    }
  }

  /**
   * 引导弹窗关闭后的处理
   */
  function onGuidanceDismissed(config) {
    localStorage.setItem(`guidance_dismissed_${config.action}`, Date.now().toString())
  }

  return {
    enabled,
    debug,
    constraints,
    beforeAction,
    showGuidanceModal,
    registerConstraint,
    registerGuidanceCallback
  }
}

/**
 * 引导弹窗类 (用于 Vue 中直接调用)
 */
class GuidanceModal {
  constructor(options = {}) {
    this.title = options.title || '操作受限'
    this.message = options.message || ''
    this.icon = options.icon || '⚠️'
    this.guidance = options.guidance || {}
    this.onAction = options.onAction || (() => {})
    this.onDismiss = options.onDismiss || (() => {})
    this.modalId = 'guidance-modal-' + Date.now()
  }

  show() {
    const modalHtml = `
      <div class="guidance-modal" id="${this.modalId}">
        <div class="guidance-overlay"></div>
        <div class="guidance-dialog">
          <div class="guidance-header">
            <span class="guidance-icon">${this.icon}</span>
            <h3 class="guidance-title">${this.escapeHtml(this.title)}</h3>
            <button class="guidance-close" aria-label="关闭">×</button>
          </div>
          <div class="guidance-body">
            <p class="guidance-message">${this.escapeHtml(this.message)}</p>
          </div>
          <div class="guidance-footer">
            <button class="guidance-action primary">
              ${this.guidance.icon ? `<span class="action-icon">${this.guidance.icon}</span>` : ''}
              <span class="action-label">${this.guidance.label || '确定'}</span>
            </button>
            <button class="guidance-dismiss">取消</button>
          </div>
        </div>
      </div>
    `

    document.body.insertAdjacentHTML('beforeend', modalHtml)
    this.bindEvents()
    requestAnimationFrame(() => {
      document.getElementById(this.modalId)?.classList.add('show')
    })
  }

  bindEvents() {
    const modal = document.getElementById(this.modalId)
    if (!modal) return

    modal.querySelector('.guidance-overlay')?.addEventListener('click', () => this.hide())
    modal.querySelector('.guidance-close')?.addEventListener('click', () => this.hide())
    modal.querySelector('.guidance-dismiss')?.addEventListener('click', () => this.hide())
    modal.querySelector('.guidance-action')?.addEventListener('click', () => {
      this.hide()
      this.onAction()
    })

    this._escHandler = (e) => {
      if (e.key === 'Escape' && document.getElementById(this.modalId)) this.hide()
    }
    document.addEventListener('keydown', this._escHandler)
  }

  hide() {
    document.removeEventListener('keydown', this._escHandler)
    const modal = document.getElementById(this.modalId)
    if (modal) {
      modal.classList.remove('show')
      setTimeout(() => {
        modal.remove()
        this.onDismiss()
      }, 200)
    }
  }

  escapeHtml(text) {
    const div = document.createElement('div')
    div.textContent = text
    return div.innerHTML
  }
}

// 导出 GuidanceModal 供 standalone 使用
export { GuidanceModal }
