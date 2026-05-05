/**
 * GuidanceEngine - 事件驱动新手引导引擎
 *
 * 核心功能：
 * - 引导事件注册与触发
 * - 引导步骤管理 (Tour)
 * - 引导状态持久化 (localStorage)
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// 引导事件配置
export const GUIDANCE_EVENTS = {
  USER_REGISTERED: 'user_registered',
  TEAM_JOINED: 'team_joined',
  FIRST_FILE_UPLOADED: 'first_file_uploaded',
  MEMBER_INVITED: 'member_invited',
  WORKFLOW_EXECUTED: 'workflow_executed',
  QUOTA_WARNING: 'quota_warning',
  PRIVATE_SPACE_PENDING: 'private_space_pending',
  CROSS_TEAM_COLLAB: 'cross_team_collab',
}

// 引导事件定义
const GUIDANCE_DEFINITIONS = {
  [GUIDANCE_EVENTS.USER_REGISTERED]: {
    title: '欢迎使用 Hermes File Manager',
    message: '您已成功注册！首先创建一个团队或加入现有团队开始存储文件。',
    actions: [
      { label: '创建我的团队', action: 'CREATE_TEAM', icon: '👥' },
      { label: '浏览现有团队', action: 'LIST_TEAMS', icon: '🔍' }
    ],
    condition: (ctx) => ctx.teams?.length === 0,
    priority: 100
  },

  [GUIDANCE_EVENTS.TEAM_JOINED]: {
    title: '加入团队成功！',
    message: '您已成功加入团队。现在可以开始上传文件或邀请其他成员。',
    actions: [
      { label: '上传第一个文件', action: 'UPLOAD_FILE', icon: '📤' },
      { label: '邀请成员', action: 'INVITE_MEMBER', icon: '👥' }
    ],
    condition: (ctx) => ctx.isFirstJoin === true,
    priority: 90
  },

  [GUIDANCE_EVENTS.FIRST_FILE_UPLOADED]: {
    title: '文件上传成功！',
    message: '了解如何与团队成员协作编辑和分享文件。',
    actions: [
      { label: '分享给成员', action: 'SHARE_FILE', icon: '🔗' },
      { label: '查看版本历史', action: 'VIEW_VERSIONS', icon: '📜' },
      { label: '创建工作流', action: 'CREATE_WORKFLOW', icon: '⚙️' }
    ],
    condition: (ctx) => ctx.uploadCount === 1,
    priority: 80
  },

  [GUIDANCE_EVENTS.MEMBER_INVITED]: {
    title: '邀请已发送',
    message: '您已成功邀请成员。了解如何设置他们的权限。',
    actions: [
      { label: '设置权限', action: 'SET_PERMISSIONS', icon: '🔐' },
      { label: '查看团队', action: 'VIEW_TEAM', icon: '👥' }
    ],
    condition: (ctx) => ctx.memberCount > 1,
    priority: 70
  },

  [GUIDANCE_EVENTS.WORKFLOW_EXECUTED]: {
    title: '工作流执行成功！',
    message: '您已成功执行第一个工作流。探索笔记本功能来记录工作流程。',
    actions: [
      { label: '创建笔记本', action: 'CREATE_NOTEBOOK', icon: '📓' },
      { label: '查看工作流', action: 'VIEW_WORKFLOWS', icon: '⚙️' }
    ],
    condition: (ctx) => ctx.workflowCount === 1,
    priority: 60
  },

  [GUIDANCE_EVENTS.QUOTA_WARNING]: {
    title: '存储空间即将用尽',
    message: '您的团队存储配额已超过 80%。请及时清理或申请扩容。',
    actions: [
      { label: '查看回收站', action: 'VIEW_TRASH', icon: '🗑️' },
      { label: '申请扩容', action: 'REQUEST_QUOTA', icon: '📈' }
    ],
    condition: (ctx) => ctx.quotaUsage > 0.8,
    priority: 95,
    autoShow: true
  },

  [GUIDANCE_EVENTS.PRIVATE_SPACE_PENDING]: {
    title: '私人空间申请待审核',
    message: '您的私人空间申请正在等待团队所有者审核。期间您可以先创建笔记。',
    actions: [
      { label: '创建笔记', action: 'CREATE_NOTEBOOK', icon: '📓' },
      { label: '查看申请状态', action: 'VIEW_REQUEST', icon: '📋' }
    ],
    condition: (ctx) => ctx.spaceStatus === 'pending',
    priority: 50
  },

  [GUIDANCE_EVENTS.CROSS_TEAM_COLLAB]: {
    title: '跨团队协作已建立',
    message: '您已与另一个团队建立协作关系。探索高级功能提升协作效率。',
    actions: [
      { label: '开启协作会话', action: 'START_COLLAB', icon: '🤝' },
      { label: '查看协作者', action: 'VIEW_COLLAB', icon: '👥' }
    ],
    condition: (ctx) => ctx.crossTeamCount > 0,
    priority: 40
  }
}

// 工作流引导步骤
export const WORKFLOW_GUIDE_STEPS = [
  { target: '#workflowTab', content: '点击「工作流」标签', position: 'bottom' },
  { target: '#newWorkflowBtn', content: '点击「+ 新建工作流」', position: 'bottom' },
  { target: '#workflowTemplate', content: '选择「文件归档流程」模板', position: 'right' },
  { target: '#workflowSave', content: '配置步骤并保存', position: 'top' }
]

// 笔记本引导步骤
export const NOTEBOOK_GUIDE_STEPS = [
  { target: '#notebookTab', content: '点击「笔记本」标签', position: 'bottom' },
  { target: '#newNotebookBtn', content: '点击「+ 新建笔记本」', position: 'bottom' },
  { target: '#notebookName', content: '输入笔记本名称', position: 'right' },
  { target: '#notebookSave', content: '保存笔记本', position: 'top' }
]

export const useGuidanceStore = defineStore('guidance', () => {
  // 状态
  const enabled = ref(true)
  const debug = ref(false)

  // 引导上下文
  const context = ref({
    teams: [],
    isFirstJoin: false,
    uploadCount: 0,
    memberCount: 0,
    workflowCount: 0,
    quotaUsage: 0,
    spaceStatus: null,
    crossTeamCount: 0
  })

  // 引导弹窗状态
  const modalVisible = ref(false)
  const modalConfig = ref({
    title: '',
    message: '',
    icon: '💡',
    actions: []
  })

  // 当前正在显示的引导事件名称
  const currentEventName = ref('')

  // 当前进行中的 Tour
  const currentTour = ref(null)
  const tourStepIndex = ref(0)

  // 引导状态持久化
  const STORAGE_KEY = 'hermes_guidance_dismissed'
  const dismissedEvents = ref(new Set(loadDismissed()))

  // 已触发的事件（防止重复触发）
  const triggeredEvents = ref(new Set())

  // T4: 引导数据统计分析
  const guidanceStats = ref({
    triggered: {},      // { eventName: count } - 触发次数
    completed: {},      // { eventName: count } - 完成次数
    dismissed: {},      // { eventName: count } - 跳过次数
    actionCounts: {},   // { actionName: count } - 各操作点击次数
    sessionStart: Date.now(),
    lastSync: null
  })

  // 统计数据持久化
  const STATS_STORAGE_KEY = 'hermes_guidance_stats'

  // 加载统计数据
  function loadStats() {
    try {
      const stored = localStorage.getItem(STATS_STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        // 合并历史数据和当前 session
        return {
          triggered: { ...parsed.triggered },
          completed: { ...parsed.completed },
          dismissed: { ...parsed.dismissed },
          actionCounts: { ...parsed.actionCounts },
          sessionStart: Date.now(),
          lastSync: parsed.lastSync
        }
      }
    } catch {}
    return guidanceStats.value
  }

  // 保存统计数据
  function saveStats() {
    try {
      localStorage.setItem(STATS_STORAGE_KEY, JSON.stringify(guidanceStats.value))
    } catch {}
  }

  // 记录引导触发
  function recordTrigger(eventName) {
    guidanceStats.value.triggered[eventName] = (guidanceStats.value.triggered[eventName] || 0) + 1
    saveStats()
  }

  // 记录引导完成
  function recordComplete(eventName) {
    guidanceStats.value.completed[eventName] = (guidanceStats.value.completed[eventName] || 0) + 1
    saveStats()
  }

  // 记录引导跳过
  function recordDismiss(eventName) {
    guidanceStats.value.dismissed[eventName] = (guidanceStats.value.dismissed[eventName] || 0) + 1
    saveStats()
  }

  // 记录操作点击
  function recordAction(actionName) {
    guidanceStats.value.actionCounts[actionName] = (guidanceStats.value.actionCounts[actionName] || 0) + 1
    saveStats()
  }

  // 异步发送到后端
  async function syncStatsToBackend() {
    if (guidanceStats.value.lastSync && Date.now() - guidanceStats.value.lastSync < 60000) {
      // 1分钟内不重复同步
      return
    }

    try {
      const token = localStorage.getItem('hfm_token')
      if (!token) return

      const statsPayload = {
        triggered: guidanceStats.value.triggered,
        completed: guidanceStats.value.completed,
        dismissed: guidanceStats.value.dismissed,
        actionCounts: guidanceStats.value.actionCounts,
        sessionDurationMs: Date.now() - guidanceStats.value.sessionStart
      }

      const res = await fetch(`${import.meta.env.VITE_API_BASE || '/api/v1'}/analytics/guidance`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(statsPayload)
      })

      if (res.ok) {
        guidanceStats.value.lastSync = Date.now()
        saveStats()
      }
    } catch (e) {
      console.error('[GuidanceStats] Failed to sync:', e)
    }
  }

  // 初始化统计数据
  guidanceStats.value = loadStats()

  // 页面 unload 时同步统计
  if (typeof window !== 'undefined') {
    window.addEventListener('beforeunload', () => {
      syncStatsToBackend()
    })
  }

  // 加载已忽略的引导
  function loadDismissed() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      return stored ? JSON.parse(stored) : []
    } catch {
      return []
    }
  }

  // 保存已忽略的引导
  function saveDismissed() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify([...dismissedEvents.value]))
    } catch {}
  }

  // 更新引导上下文
  function updateContext(updates) {
    context.value = { ...context.value, ...updates }
  }

  // 检查事件是否已触发过
  function isTriggered(eventName) {
    return triggeredEvents.value.has(eventName)
  }

  // 检查事件是否被用户忽略
  function isDismissed(eventName) {
    return dismissedEvents.value.has(eventName)
  }

  // 注册事件触发
  function registerTriggered(eventName) {
    triggeredEvents.value.add(eventName)
  }

  // 触发引导事件
  function trigger(eventName, eventContext = {}) {
    if (!enabled.value) return false

    // 标准化事件名称（支持大小写不敏感）
    const normalizedEvent = eventName?.toLowerCase()

    // 更新上下文
    updateContext(eventContext)

    // 检查是否已触发或已忽略
    if (isDismissed(eventName)) {
      debug.value && console.log(`[Guidance] Event dismissed: ${eventName}`)
      return false
    }

    // 获取事件配置（大小写不敏感）
    let config = GUIDANCE_DEFINITIONS[eventName]

    // 如果没找到，尝试通过 GUIDANCE_EVENTS 映射
    if (!config) {
      // 查找匹配的 GUIDANCE_EVENTS 键
      const matchedKey = Object.entries(GUIDANCE_EVENTS).find(([k, v]) =>
        k.toLowerCase() === normalizedEvent || v.toLowerCase() === normalizedEvent
      )?.[1]

      if (matchedKey) {
        config = GUIDANCE_DEFINITIONS[matchedKey]
        eventName = matchedKey
      }
    }

    if (!config) {
      debug.value && console.log(`[Guidance] Unknown event: ${eventName}`)
      return false
    }

    // 检查触发条件
    if (config.condition && !config.condition(context.value)) {
      debug.value && console.log(`[Guidance] Condition not met: ${eventName}`)
      return false
    }

    // 标记为已触发
    registerTriggered(eventName)

    // T4: 记录引导触发统计
    recordTrigger(eventName)

    // 设置当前事件名称
    currentEventName.value = eventName

    // 显示引导弹窗
    showGuidance(config)

    return true
  }

  // 显示引导弹窗
  function showGuidance(config) {
    modalConfig.value = {
      title: config.title,
      message: config.message,
      icon: config.icon || '💡',
      actions: config.actions || []
    }
    modalVisible.value = true
  }

  // 关闭引导弹窗
  function dismiss(eventName) {
    if (eventName) {
      dismissedEvents.value.add(eventName)
      saveDismissed()
      // T4: 记录引导跳过统计
      recordDismiss(eventName)
    }
    currentEventName.value = ''
    modalVisible.value = false
  }

  // 执行引导操作
  function executeAction(action) {
    const actions = {
      'CREATE_TEAM': () => navigateTo('/teams/create'),
      'LIST_TEAMS': () => navigateTo('/teams'),
      'UPLOAD_FILE': () => navigateTo('/upload'),
      'SHARE_FILE': () => openShareDialog(),
      'VIEW_VERSIONS': () => navigateTo('/versions'),
      'CREATE_WORKFLOW': () => {
      window.dispatchEvent(new CustomEvent('guidance:workflow-tour'))
      navigateTo('/workflows/create')
    },
      'INVITE_MEMBER': () => navigateTo('/teams/invite'),
      'SET_PERMISSIONS': () => navigateTo('/teams/permissions'),
      'VIEW_TEAM': () => navigateTo('/teams'),
      'CREATE_NOTEBOOK': () => {
      window.dispatchEvent(new CustomEvent('guidance:notebook-tour'))
      navigateTo('/notebooks/create')
    },
      'VIEW_WORKFLOWS': () => navigateTo('/workflows'),
      'VIEW_TRASH': () => navigateTo('/trash'),
      'REQUEST_QUOTA': () => navigateTo('/settings/quota'),
      'VIEW_REQUEST': () => navigateTo('/requests'),
      'START_COLLAB': () => openCollabDialog(),
      'VIEW_COLLAB': () => navigateTo('/collaborations'),
    }

    const handler = actions[action]
    if (handler) {
      // T4: 记录操作点击统计
      recordAction(action)
      handler()
      modalVisible.value = false
    }
  }

  // 导航
  function navigateTo(path) {
    window.location.hash = path
  }

  // 打开分享对话框
  function openShareDialog() {
    // 触发全局事件或调用已有组件
    window.dispatchEvent(new CustomEvent('guidance:open-share'))
  }

  // 打开协作对话框
  function openCollabDialog() {
    window.dispatchEvent(new CustomEvent('guidance:open-collab'))
  }

  // 开始 Tour
  function startTour(tourId, steps) {
    currentTour.value = {
      id: tourId,
      steps: steps,
      stepIndex: 0
    }
    tourStepIndex.value = 0
    showTourStep(0)
  }

  // 显示 Tour 步骤
  function showTourStep(index) {
    if (!currentTour.value) return
    const step = currentTour.value.steps[index]
    if (!step) {
      endTour()
      return
    }
    // 这里可以集成 shepherd.js 或 intro.js 的 Tour 功能
    console.log(`[Tour] Step ${index + 1}:`, step.content)
    tourStepIndex.value = index
  }

  // 下一步
  function nextStep() {
    if (!currentTour.value) return
    const nextIndex = tourStepIndex.value + 1
    if (nextIndex >= currentTour.value.steps.length) {
      endTour()
    } else {
      showTourStep(nextIndex)
    }
  }

  // 上一步
  function prevStep() {
    if (!currentTour.value) return
    const prevIndex = tourStepIndex.value - 1
    if (prevIndex < 0) return
    showTourStep(prevIndex)
  }

  // 结束 Tour
  function endTour() {
    currentTour.value = null
    tourStepIndex.value = 0
  }

  // 重置引导状态（用于测试）
  function resetGuidance() {
    triggeredEvents.value.clear()
    dismissedEvents.value.clear()
    localStorage.removeItem(STORAGE_KEY)
  }

  return {
    // 状态
    enabled,
    debug,
    context,
    modalVisible,
    modalConfig,
    currentEventName,
    currentTour,
    tourStepIndex,
    guidanceStats,
    // 方法
    updateContext,
    trigger,
    dismiss,
    executeAction,
    startTour,
    nextStep,
    prevStep,
    endTour,
    resetGuidance,
    syncStatsToBackend,
    // T4: 统计方法
    recordTrigger,
    recordComplete,
    recordDismiss,
    recordAction,
    // 常量
    GUIDANCE_EVENTS,
    GUIDANCE_DEFINITIONS,
    WORKFLOW_GUIDE_STEPS,
    NOTEBOOK_GUIDE_STEPS
  }
})

// 延迟创建 store 实例（Pinia 安装后才会调用）
let guidanceStoreInstance = null
const getGuidanceStore = () => {
  if (!guidanceStoreInstance) {
    guidanceStoreInstance = useGuidanceStore()
  }
  return guidanceStoreInstance
}

// 暴露到 window，供 Vanilla JS 引导系统调用
if (typeof window !== 'undefined') {
  // 创建代理对象，平滑 triggerGuidance 调用
  window.__vueGuidance = {
    trigger: (event, context) => getGuidanceStore().trigger(event, context),
    dismiss: (event) => getGuidanceStore().dismiss(event),
    executeAction: (action) => getGuidanceStore().executeAction(action),
    startTour: (tourId, steps) => getGuidanceStore().startTour(tourId, steps),
    resetGuidance: () => getGuidanceStore().resetGuidance(),
    // 直接访问 store 方法
    get store() { return getGuidanceStore() }
  }

  // 兼容旧版 Vanilla JS 引导系统
  window.guidance = window.__vueGuidance
  window.triggerGuidance = (event, context) => getGuidanceStore().trigger(event, context)

  // 监听 Vanilla JS 系统触发的引导事件
  window.addEventListener('guidance:trigger', (e) => {
    const { event, context } = e.detail || {}
    if (event) {
      getGuidanceStore().trigger(event, context)
    }
  })

  console.log('[VueGuidance] Initialized and exposed to window.__vueGuidance and window.guidance')
}
