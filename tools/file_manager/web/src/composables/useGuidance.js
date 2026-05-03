/**
 * Composable: useGuidance
 *
 * 提供引导引擎的响应式接口
 *
 * 使用方式:
 * import { useGuidance } from '@/composables/useGuidance'
 * const { trigger, context } = useGuidance()
 *
 * trigger('user_registered', { teams: [] })
 */

import { computed } from 'vue'
import { useGuidanceStore, GUIDANCE_EVENTS, GUIDANCE_DEFINITIONS } from '@/stores/guidanceStore'

export function useGuidance() {
  const store = useGuidanceStore()

  // 响应式上下文
  const context = computed(() => store.context)

  // 当前弹窗状态
  const isModalVisible = computed(() => store.modalVisible)
  const modalConfig = computed(() => store.modalConfig)

  // 当前 Tour
  const currentTour = computed(() => store.currentTour)
  const tourStepIndex = computed(() => store.tourStepIndex)

  // 触发引导事件
  function trigger(eventName, eventContext = {}) {
    return store.trigger(eventName, eventContext)
  }

  // 触发用户注册引导
  function onUserRegistered(userContext = {}) {
    return trigger(GUIDANCE_EVENTS.USER_REGISTERED, {
      teams: userContext.teams || [],
      ...userContext
    })
  }

  // 触发加入团队引导
  function onTeamJoined(isFirstJoin = true) {
    return trigger(GUIDANCE_EVENTS.TEAM_JOINED, {
      isFirstJoin,
      teamId: isFirstJoin ? null : undefined
    })
  }

  // 触发首次文件上传引导
  function onFirstFileUploaded(uploadCount = 1) {
    return trigger(GUIDANCE_EVENTS.FIRST_FILE_UPLOADED, {
      uploadCount
    })
  }

  // 触发成员邀请引导
  function onMemberInvited(memberCount = 2) {
    return trigger(GUIDANCE_EVENTS.MEMBER_INVITED, {
      memberCount
    })
  }

  // 触发工作流执行引导
  function onWorkflowExecuted(workflowCount = 1) {
    return trigger(GUIDANCE_EVENTS.WORKFLOW_EXECUTED, {
      workflowCount
    })
  }

  // 触发配额警告引导
  function onQuotaWarning(quotaUsage = 0.85) {
    return trigger(GUIDANCE_EVENTS.QUOTA_WARNING, {
      quotaUsage
    })
  }

  // 触发私人空间申请引导
  function onPrivateSpacePending(spaceStatus = 'pending') {
    return trigger(GUIDANCE_EVENTS.PRIVATE_SPACE_PENDING, {
      spaceStatus
    })
  }

  // 触发跨团队协作引导
  function onCrossTeamCollab(crossTeamCount = 1) {
    return trigger(GUIDANCE_EVENTS.CROSS_TEAM_COLLAB, {
      crossTeamCount
    })
  }

  // 关闭弹窗
  function dismiss(eventName) {
    store.dismiss(eventName)
  }

  // 执行引导操作
  function executeAction(action) {
    store.executeAction(action)
  }

  // 开始工作流引导 Tour
  function startWorkflowGuide() {
    store.startTour('workflow_guide', [
      { target: '#workflowTab', content: '点击「工作流」标签', position: 'bottom' },
      { target: '#newWorkflowBtn', content: '点击「+ 新建工作流」', position: 'bottom' },
      { target: '#workflowTemplate', content: '选择模板', position: 'right' },
      { target: '#workflowSave', content: '保存', position: 'top' }
    ])
  }

  // 开始笔记本引导 Tour
  function startNotebookGuide() {
    store.startTour('notebook_guide', [
      { target: '#notebookTab', content: '点击「笔记本」标签', position: 'bottom' },
      { target: '#newNotebookBtn', content: '点击「+ 新建笔记本」', position: 'bottom' },
      { target: '#notebookName', content: '输入名称', position: 'right' },
      { target: '#notebookSave', content: '保存', position: 'top' }
    ])
  }

  // 导航辅助
  function navigateTo(path) {
    store.navigateTo(path)
  }

  return {
    // 状态
    context,
    isModalVisible,
    modalConfig,
    currentTour,
    tourStepIndex,
    // 事件触发
    trigger,
    onUserRegistered,
    onTeamJoined,
    onFirstFileUploaded,
    onMemberInvited,
    onWorkflowExecuted,
    onQuotaWarning,
    onPrivateSpacePending,
    onCrossTeamCollab,
    // 操作
    dismiss,
    executeAction,
    startWorkflowGuide,
    startNotebookGuide,
    navigateTo,
    // 常量
    GUIDANCE_EVENTS,
    GUIDANCE_DEFINITIONS
  }
}

// 导出 GuidanceEngine 类（用于需要类语义的场景）
export class GuidanceEngine {
  constructor() {
    this.store = useGuidanceStore()
  }

  trigger(eventName, context) {
    return this.store.trigger(eventName, context)
  }

  registerEvent(eventName, config) {
    // 可以动态注册新的引导事件
    console.log('[GuidanceEngine] Register event:', eventName, config)
  }
}
