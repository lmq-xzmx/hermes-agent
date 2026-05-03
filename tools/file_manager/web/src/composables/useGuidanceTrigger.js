/**
 * useGuidanceTrigger - 引导触发点集成 composable
 *
 * 在用户关键操作时自动触发引导事件
 */
import { useGuidanceStore, GUIDANCE_EVENTS } from '@/stores/guidanceStore'

export function useGuidanceTrigger() {
  const guidanceStore = useGuidanceStore()

  /**
   * 用户注册后触发
   */
  function onUserRegistered(user) {
    guidanceStore.trigger(GUIDANCE_EVENTS.USER_REGISTERED, {
      userId: user.id,
      teams: []
    })
  }

  /**
   * 用户加入团队后触发
   */
  function onTeamJoined(team, isFirstJoin = false) {
    guidanceStore.trigger(GUIDANCE_EVENTS.TEAM_JOINED, {
      teamId: team.id,
      teamName: team.name,
      isFirstJoin
    })
  }

  /**
   * 用户上传第一个文件后触发
   */
  function onFirstFileUploaded(file, space) {
    guidanceStore.trigger(GUIDANCE_EVENTS.FIRST_FILE_UPLOADED, {
      fileId: file.id,
      fileName: file.name,
      spaceId: space.id,
      uploadCount: 1
    })
  }

  /**
   * 用户上传文件后触发（累计）
   */
  function onFileUploaded(file, space, totalCount) {
    guidanceStore.trigger(GUIDANCE_EVENTS.FIRST_FILE_UPLOADED, {
      fileId: file.id,
      fileName: file.name,
      spaceId: space.id,
      uploadCount: totalCount
    })
  }

  /**
   * 用户邀请成员后触发
   */
  function onMemberInvited(member, team) {
    guidanceStore.trigger(GUIDANCE_EVENTS.MEMBER_INVITED, {
      memberId: member.id,
      memberName: member.username,
      teamId: team.id,
      memberCount: team.memberCount
    })
  }

  /**
   * 用户执行工作流后触发
   */
  function onWorkflowExecuted(workflow, result) {
    guidanceStore.trigger(GUIDANCE_EVENTS.WORKFLOW_EXECUTED, {
      workflowId: workflow.id,
      workflowName: workflow.name,
      workflowCount: 1
    })
  }

  /**
   * 配额警告触发
   */
  function onQuotaWarning(space, usageRate) {
    guidanceStore.trigger(GUIDANCE_EVENTS.QUOTA_WARNING, {
      spaceId: space.id,
      spaceName: space.name,
      quotaUsage: usageRate
    })
  }

  /**
   * 私人空间申请待审核触发
   */
  function onPrivateSpacePending(space) {
    guidanceStore.trigger(GUIDANCE_EVENTS.PRIVATE_SPACE_PENDING, {
      spaceId: space.id,
      spaceName: space.name,
      spaceStatus: 'pending'
    })
  }

  /**
   * 跨团队协作建立触发
   */
  function onCrossTeamCollaboration(team1, team2) {
    guidanceStore.trigger(GUIDANCE_EVENTS.CROSS_TEAM_COLLAB, {
      team1Id: team1.id,
      team2Id: team2.id,
      crossTeamCount: 1
    })
  }

  return {
    onUserRegistered,
    onTeamJoined,
    onFirstFileUploaded,
    onFileUploaded,
    onMemberInvited,
    onWorkflowExecuted,
    onQuotaWarning,
    onPrivateSpacePending,
    onCrossTeamCollaboration
  }
}
