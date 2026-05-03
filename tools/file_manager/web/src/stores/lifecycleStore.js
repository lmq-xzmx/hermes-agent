/**
 * Pinia Store: 生命周期约束管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useLifecycleStore = defineStore('lifecycle', () => {
  // 状态
  const enabled = ref(true)
  const debug = ref(false)

  // 约束规则
  const constraints = ref(new Map())
  const guidanceCallbacks = ref(new Map())

  // 当前引导弹窗状态
  const modalVisible = ref(false)
  const modalConfig = ref({
    title: '操作受限',
    message: '',
    icon: '⚠️',
    guidance: {}
  })

  // 初始化默认约束
  function initDefaultConstraints() {
    const c = new Map()

    c.set('upload_file', {
      check: async (ctx) => ctx.isMember && ctx.hasQuota,
      error: {
        title: '无法上传文件',
        message: '您还没有加入任何团队，无法上传文件。请先加入一个团队或创建一个新团队。',
        icon: '📤'
      },
      guidance: { label: '加入团队', icon: '👥', path: '/teams' }
    })

    c.set('create_team', {
      check: async (ctx) => ctx.hasAvailablePool,
      error: {
        title: '无法创建团队',
        message: '系统暂无可用存储池，无法创建新团队。请联系管理员创建存储池后再试。',
        icon: '👥'
      },
      guidance: { label: '联系管理员', icon: '📧', action: 'showContactAdminModal' }
    })

    c.set('create_private_space', {
      check: async (ctx) => ctx.isTeamMember,
      error: {
        title: '无法创建私人空间',
        message: '只有团队成员才能申请私人空间。',
        icon: '🔒'
      },
      guidance: { label: '加入团队', icon: '👥', path: '/teams' }
    })

    c.set('delete_pool', {
      check: async (ctx) => ctx.teamCount === 0,
      error: {
        title: '无法删除存储池',
        message: '该存储池仍有团队使用，无法删除。请先将团队迁移到其他存储池。',
        icon: '⚠️'
      },
      guidance: { label: '查看团队', icon: '👥', path: '/admin/teams' }
    })

    c.set('delete_space', {
      check: async (ctx) => ctx.memberCount === 0 && ctx.isOwner,
      error: {
        title: '无法删除空间',
        message: '该空间仍有成员，无法删除。请先移除所有成员。',
        icon: '👥'
      },
      guidance: { label: '查看成员', icon: '👥', path: '/admin/members' }
    })

    c.set('delete_team', {
      check: async (ctx) => ctx.isOwner,
      error: {
        title: '无法删除团队',
        message: '只有团队所有者可以删除团队。',
        icon: '👥'
      },
      guidance: { label: '联系管理员', icon: '📧', action: 'showContactAdminModal' }
    })

    c.set('invite_member', {
      check: async (ctx) => ctx.isOwner,
      error: {
        title: '无法邀请成员',
        message: '只有空间所有者可以邀请新成员。',
        icon: '👥'
      },
      guidance: { label: '联系管理员', icon: '📧', action: 'showContactAdminModal' }
    })

    c.set('check_quota', {
      check: async (ctx) => ctx.sufficientQuota,
      error: {
        title: '配额不足',
        message: '存储配额已用尽，无法上传新文件。请清理回收站或联系管理员申请扩容。',
        icon: '💾'
      },
      guidance: { label: '查看回收站', icon: '🗑️', path: '/trash' }
    })

    c.set('update_quota', {
      check: async (ctx) => ctx.isOwner,
      error: {
        title: '无法修改配额',
        message: '只有空间所有者可以修改配额。',
        icon: '💾'
      },
      guidance: { label: '联系管理员', icon: '📧', action: 'showContactAdminModal' }
    })

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

  // 初始化
  initDefaultConstraints()

  // 注册约束
  function registerConstraint(action, config) {
    const c = new Map(constraints.value)
    c.set(action, config)
    constraints.value = c
  }

  // 注册引导回调
  function registerGuidanceCallback(action, callback) {
    const c = new Map(guidanceCallbacks.value)
    c.set(action, callback)
    guidanceCallbacks.value = c
  }

  // 检查约束
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

  // 显示引导弹窗 (统一入口，支持两种格式)
  // 格式1: beforeAction 返回 { error: {title, message, icon}, guidance: {...} }
  // 格式2: LifecycleInterceptor 返回 { code, message, details, guidance, error: {title, icon} }
  function showGuidance(config) {
    // 适配两种格式
    const title = config.error?.title || config.error?.message || '操作受限'
    const message = config.error?.message || config.message || ''
    const icon = config.error?.icon || '⚠️'

    modalConfig.value = {
      title,
      message,
      icon,
      guidance: config.guidance || {},
      code: config.code // 保留错误码用于日志
    }
    modalVisible.value = true
  }

  // 兼容旧方法名
  function showGuidanceModal(config) {
    showGuidance(config)
  }

  // 执行引导操作
  function executeGuidance(guidance) {
    if (guidance.path) {
      window.location.hash = guidance.path
    } else if (guidance.action) {
      const callback = guidanceCallbacks.value.get(guidance.action)
      if (callback) callback()
    }
  }

  // 关闭弹窗
  function closeModal() {
    modalVisible.value = false
  }

  // 关闭弹窗（带"不再显示"标记，仅对当前会话生效）
  // 注意：生命周期约束基于上下文，不适合永久忽略
  function dismissGuidance() {
    modalVisible.value = false
  }

  return {
    // 状态
    enabled,
    debug,
    modalVisible,
    modalConfig,
    // 方法
    registerConstraint,
    registerGuidanceCallback,
    beforeAction,
    showGuidance,       // 统一入口
    showGuidanceModal,  // 兼容旧方法
    closeModal,
    dismissGuidance,
    executeGuidance
  }
})
