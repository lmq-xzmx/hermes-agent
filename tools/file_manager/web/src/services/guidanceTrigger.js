/**
 * GuidanceTrigger - 引导事件触发点集成
 *
 * 在关键操作后触发对应的引导事件
 * 使用方式:
 *   import { useGuidanceTrigger } from '@/services/guidanceTrigger'
 *   const trigger = useGuidanceTrigger()
 *   trigger.onUploadSuccess({ uploadCount: 1 })
 */

import { useGuidanceStore, GUIDANCE_EVENTS } from '@/stores/guidanceStore'

// 引导触发器单例
let _instance = null

export function useGuidanceTrigger() {
  if (!_instance) {
    _instance = new GuidanceTrigger()
  }
  return _instance
}

class GuidanceTrigger {
  constructor() {
    this.store = useGuidanceStore()
    this._initialized = false
  }

  /**
   * 初始化触发点监听
   * 在应用启动时调用一次
   */
  init() {
    if (this._initialized) return
    this._initialized = true

    // 监听文件上传成功事件
    window.addEventListener('file:uploaded', (e) => {
      this.onFileUploaded(e.detail)
    })

    // 监听团队加入事件
    window.addEventListener('team:joined', (e) => {
      this.onTeamJoined(e.detail)
    })

    // 监听成员邀请事件
    window.addEventListener('member:invited', (e) => {
      this.onMemberInvited(e.detail)
    })

    // 监听工作流执行事件
    window.addEventListener('workflow:executed', (e) => {
      this.onWorkflowExecuted(e.detail)
    })

    // 监听配额警告事件
    window.addEventListener('quota:warning', (e) => {
      this.onQuotaWarning(e.detail)
    })

    // 监听注册事件
    window.addEventListener('user:registered', (e) => {
      this.onUserRegistered(e.detail)
    })

    console.log('[GuidanceTrigger] Initialized')
  }

  /**
   * 用户注册成功
   */
  onUserRegistered(detail = {}) {
    const { teams = [] } = detail
    this.store.trigger(GUIDANCE_EVENTS.USER_REGISTERED, {
      teams,
      isFirstUser: teams.length === 0
    })
  }

  /**
   * 加入团队成功
   */
  onTeamJoined(detail = {}) {
    const { isFirstJoin = true, memberCount = 1 } = detail
    this.store.trigger(GUIDANCE_EVENTS.TEAM_JOINED, {
      isFirstJoin,
      memberCount
    })
  }

  /**
   * 文件上传成功
   */
  onFileUploaded(detail = {}) {
    const { uploadCount = 1, spaceId, fileName } = detail
    this.store.trigger(GUIDANCE_EVENTS.FIRST_FILE_UPLOADED, {
      uploadCount,
      spaceId,
      fileName
    })
  }

  /**
   * 成员邀请成功
   */
  onMemberInvited(detail = {}) {
    const { memberCount = 2, invitedUser } = detail
    this.store.trigger(GUIDANCE_EVENTS.MEMBER_INVITED, {
      memberCount,
      invitedUser
    })
  }

  /**
   * 工作流执行成功
   */
  onWorkflowExecuted(detail = {}) {
    const { workflowCount = 1, workflowId, workflowName } = detail
    this.store.trigger(GUIDANCE_EVENTS.WORKFLOW_EXECUTED, {
      workflowCount,
      workflowId,
      workflowName
    })
  }

  /**
   * 配额警告
   */
  onQuotaWarning(detail = {}) {
    const { quotaUsage = 0.85, spaceId, spaceName } = detail
    this.store.trigger(GUIDANCE_EVENTS.QUOTA_WARNING, {
      quotaUsage,
      spaceId,
      spaceName
    })
  }

  /**
   * 私人空间申请状态变更
   */
  onPrivateSpacePending(detail = {}) {
    const { spaceStatus = 'pending', spaceId } = detail
    this.store.trigger(GUIDANCE_EVENTS.PRIVATE_SPACE_PENDING, {
      spaceStatus,
      spaceId
    })
  }

  /**
   * 跨团队协作建立
   */
  onCrossTeamCollab(detail = {}) {
    const { crossTeamCount = 1, collaboratorId } = detail
    this.store.trigger(GUIDANCE_EVENTS.CROSS_TEAM_COLLAB, {
      crossTeamCount,
      collaboratorId
    })
  }

  /**
   * 触发自定义事件
   */
  triggerEvent(eventName, detail = {}) {
    this.store.trigger(eventName, detail)
  }

  /**
   * 触发全局自定义事件（供外部调用）
   */
  static emit(eventName, detail = {}) {
    window.dispatchEvent(new CustomEvent(eventName, { detail }))
  }
}

// 导出便捷触发函数
export function triggerUpload(uploadCount) {
  GuidanceTrigger.emit('file:uploaded', { uploadCount })
}

export function triggerTeamJoin(isFirstJoin) {
  GuidanceTrigger.emit('team:joined', { isFirstJoin })
}

export function triggerMemberInvite(memberCount) {
  GuidanceTrigger.emit('member:invited', { memberCount })
}

export function triggerWorkflow(workflowCount) {
  GuidanceTrigger.emit('workflow:executed', { workflowCount })
}

export function triggerQuotaAlert(quotaUsage) {
  GuidanceTrigger.emit('quota:warning', { quotaUsage })
}

export function triggerUserReg(teams) {
  GuidanceTrigger.emit('user:registered', { teams })
}
