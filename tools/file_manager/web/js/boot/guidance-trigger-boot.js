/**
 * guidance-trigger-boot.js - 引导触发点初始化
 *
 * 在关键操作节点触发对应的引导事件
 * 依赖于 guidance-boot.js 和 guidanceEngine.js
 * 同时支持 Vue Pinia store (通过 window.__vueGuidance)
 */

/**
 * 触发引导事件的便捷函数
 * 同时触发 Vanilla JS 和 Vue 两种引导系统
 */
window.triggerGuidance = function triggerGuidance(event, context = {}) {
    let result = false

    // Vanilla JS 引导系统
    if (window.guidance) {
        result = window.guidance.trigger(event, context) || result
    }

    // Vue Pinia 引导系统 (如果可用)
    if (window.__vueGuidance) {
        window.__vueGuidance.trigger(event, context)
    }

    // 触发 DOM 事件，供 Vue 组件监听
    window.dispatchEvent(new CustomEvent('guidance:trigger', {
        detail: { event, context }
    }))

    return result
}

/**
 * 初始化引导触发点
 */
function initGuidanceTriggers() {
    // 等待 guidanceEngine 初始化
    if (!window.guidance) {
        console.warn('[GuidanceTrigger] GuidanceEngine not found, retrying...')
        setTimeout(initGuidanceTriggers, 100)
        return
    }

    console.log('[GuidanceTrigger] Initializing guidance triggers...')

    // ==================== 文件操作触发点 ====================

    // 监听文件上传成功
    window.addEventListener('file:uploaded', (e) => {
        const detail = e.detail || {}
        const uploadCount = detail.uploadCount || 1
        console.log('[GuidanceTrigger] File uploaded:', detail)
        triggerGuidance('FIRST_FILE_UPLOADED', {
            uploadCount,
            spaceId: detail.spaceId,
            fileName: detail.fileName
        })
    })

    // 监听文件分享
    window.addEventListener('file:shared', (e) => {
        const detail = e.detail || {}
        console.log('[GuidanceTrigger] File shared:', detail)
        triggerGuidance('SHARE_FILE', {
            shared: true,
            fileId: detail.fileId
        })
    })

    // ==================== 团队操作触发点 ====================

    // 监听用户注册
    window.addEventListener('user:registered', (e) => {
        const detail = e.detail || {}
        console.log('[GuidanceTrigger] User registered:', detail)
        triggerGuidance('USER_REGISTERED', {
            teams: detail.teams || [],
            isFirstUser: (detail.teams || []).length === 0
        })
    })

    // 监听加入团队
    window.addEventListener('team:joined', (e) => {
        const detail = e.detail || {}
        const isFirstJoin = detail.isFirstJoin !== false
        console.log('[GuidanceTrigger] Team joined:', detail)
        triggerGuidance('TEAM_JOINED', {
            isFirstJoin,
            teamId: detail.teamId,
            hasUploaded: false
        })
    })

    // 监听创建团队
    window.addEventListener('team:created', (e) => {
        const detail = e.detail || {}
        console.log('[GuidanceTrigger] Team created:', detail)
        // 创建团队后触发欢迎引导
        triggerGuidance('TEAM_JOINED', {
            isFirstJoin: true,
            teamId: detail.teamId,
            hasUploaded: false
        })
    })

    // ==================== 成员操作触发点 ====================

    // 监听成员邀请
    window.addEventListener('member:invited', (e) => {
        const detail = e.detail || {}
        const memberCount = detail.memberCount || 2
        console.log('[GuidanceTrigger] Member invited:', detail)
        triggerGuidance('MEMBER_INVITED', {
            memberCount,
            invitedUser: detail.invitedUser
        })
    })

    // ==================== 工作流触发点 ====================

    // 监听工作流执行
    window.addEventListener('workflow:executed', (e) => {
        const detail = e.detail || {}
        const workflowCount = detail.workflowCount || 1
        console.log('[GuidanceTrigger] Workflow executed:', detail)
        triggerGuidance('WORKFLOW_EXECUTED', {
            workflowCount,
            workflowId: detail.workflowId,
            workflowName: detail.workflowName
        })
    })

    // 监听工作流创建
    window.addEventListener('workflow:created', (e) => {
        const detail = e.detail || {}
        console.log('[GuidanceTrigger] Workflow created:', detail)
        // 工作流创建后可以触发进阶引导
        triggerGuidance('WORKFLOW_EXECUTED', {
            workflowCount: 1,
            workflowId: detail.workflowId
        })
    })

    // ==================== 笔记本触发点 ====================

    // 监听笔记本创建
    window.addEventListener('notebook:created', (e) => {
        const detail = e.detail || {}
        console.log('[GuidanceTrigger] Notebook created:', detail)
        triggerGuidance('FIRST_NOTEBOOK_CREATED', {
            notebookCreated: true,
            notebookId: detail.notebookId
        })
    })

    // ==================== 存储/配额触发点 ====================

    // 监听配额警告
    window.addEventListener('quota:warning', (e) => {
        const detail = e.detail || {}
        const quotaUsage = detail.quotaUsage || 0.85
        console.log('[GuidanceTrigger] Quota warning:', detail)
        triggerGuidance('QUOTA_WARNING', {
            quotaUsage,
            spaceId: detail.spaceId,
            spaceName: detail.spaceName
        })
    })

    // 监听私人空间申请
    window.addEventListener('private:space:requested', (e) => {
        const detail = e.detail || {}
        console.log('[GuidanceTrigger] Private space requested:', detail)
        triggerGuidance('PRIVATE_SPACE_REQUESTED', {
            privateSpaceStatus: 'pending',
            spaceId: detail.spaceId
        })
    })

    // ==================== 跨团队协作触发点 ====================

    // 监听跨团队协作建立
    window.addEventListener('collaboration:established', (e) => {
        const detail = e.detail || {}
        const crossTeamCount = detail.crossTeamCount || 1
        console.log('[GuidanceTrigger] Collaboration established:', detail)
        triggerGuidance('CROSS_TEAM_COLLABORATION', {
            crossTeamSpaces: crossTeamCount,
            collaboratorId: detail.collaboratorId
        })
    })

    // ==================== 全局便捷触发函数 ====================

    // 暴露全局便捷触发函数
    window.triggerUpload = function(uploadCount) {
        window.dispatchEvent(new CustomEvent('file:uploaded', {
            detail: { uploadCount: uploadCount || 1 }
        }))
    }

    window.triggerTeamJoin = function(teamId, isFirstJoin) {
        window.dispatchEvent(new CustomEvent('team:joined', {
            detail: { teamId, isFirstJoin: isFirstJoin !== false }
        }))
    }

    window.triggerMemberInvite = function(memberCount) {
        window.dispatchEvent(new CustomEvent('member:invited', {
            detail: { memberCount: memberCount || 2 }
        }))
    }

    window.triggerWorkflow = function(workflowId, workflowName) {
        window.dispatchEvent(new CustomEvent('workflow:executed', {
            detail: { workflowId, workflowName, workflowCount: 1 }
        }))
    }

    window.triggerQuotaAlert = function(quotaUsage) {
        window.dispatchEvent(new CustomEvent('quota:warning', {
            detail: { quotaUsage: quotaUsage || 0.85 }
        }))
    }

    window.triggerUserReg = function(teams) {
        window.dispatchEvent(new CustomEvent('user:registered', {
            detail: { teams: teams || [] }
        }))
    }

    console.log('[GuidanceTrigger] Guidance triggers initialized')
}

// DOM 加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initGuidanceTriggers)
} else {
    initGuidanceTriggers()
}
