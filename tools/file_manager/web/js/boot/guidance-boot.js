/**
 * guidance-boot.js - 引导系统初始化
 *
 * 注册所有新手引导事件
 */

// 等待 DOM 加载完成
document.addEventListener('DOMContentLoaded', () => {
    initGuidanceEvents()
})

/**
 * 初始化引导事件
 */
function initGuidanceEvents() {
    if (!window.guidance) {
        console.error('[GuidanceBoot] GuidanceEngine not found')
        return
    }

    // 注册 8 个核心引导事件
    guidance.register({

        // ==================== 阶段1: 入门 ====================

        USER_REGISTERED: {
            title: '欢迎使用 Hermes File Manager',
            message: '您已成功注册！首先创建一个团队或加入现有团队开始存储文件。',
            icon: '👋',
            condition: (ctx) => ctx.teams && ctx.teams.length === 0,
            actions: [
                { label: '创建我的团队', action: 'CREATE_TEAM', icon: '👥' },
                { label: '浏览现有团队', action: 'LIST_TEAMS', icon: '🔍' }
            ]
        },

        TEAM_JOINED: {
            title: '您已加入团队',
            message: '探索团队共享空间，上传您的第一个文件',
            icon: '🎉',
            condition: (ctx) => !ctx.hasUploaded,
            actions: [
                { label: '上传文件', action: 'UPLOAD_FILE', icon: '📤' },
                { label: '查看团队成员', action: 'VIEW_MEMBERS', icon: '👥' }
            ]
        },

        FIRST_FILE_UPLOADED: {
            title: '文件上传成功！',
            message: '了解如何与团队成员协作编辑和分享文件',
            icon: '✅',
            condition: (ctx) => ctx.uploadCount === 1,
            actions: [
                { label: '分享给成员', action: 'SHARE_FILE', icon: '🔗' },
                { label: '查看版本历史', action: 'VIEW_VERSIONS', icon: '📜' },
                { label: '创建工作流', action: 'CREATE_WORKFLOW', icon: '⚙️' }
            ]
        },

        // ==================== 阶段2: 协作 ====================

        MEMBER_INVITED: {
            title: '新成员已邀请',
            message: '了解如何设置成员权限和管理团队文件',
            icon: '🤝',
            condition: (ctx) => ctx.memberCount > 1,
            actions: [
                { label: '设置权限', action: 'SET_PERMISSIONS', icon: '🔐' },
                { label: '创建团队工作流', action: 'CREATE_TEAM_WORKFLOW', icon: '⚙️' }
            ]
        },

        WORKFLOW_EXECUTED: {
            title: '工作流执行成功',
            message: '您已完成第一个自动化工作流！探索更多高级功能',
            icon: '⚡',
            condition: (ctx) => ctx.workflowExecuted === true,
            actions: [
                { label: '查看执行记录', action: 'VIEW_EXECUTION_LOG', icon: '📋' },
                { label: '创建笔记本', action: 'CREATE_NOTEBOOK', icon: '📓' }
            ]
        },

        SHARE_FILE: {
            title: '文件已分享',
            message: '探索更多协作方式：创建工作流自动化处理，或使用笔记本记录协作心得',
            icon: '🔗',
            condition: (ctx) => ctx.shared === true,
            actions: [
                { label: '创建工作流', action: 'CREATE_WORKFLOW', icon: '⚙️' },
                { label: '创建笔记本', action: 'CREATE_NOTEBOOK', icon: '📓' }
            ]
        },

        FIRST_NOTEBOOK_CREATED: {
            title: '笔记本创建成功',
            message: '探索笔记本的高级用法：关联文件、设置提醒、邀请协作者',
            icon: '📓',
            condition: (ctx) => ctx.notebookCreated === true,
            actions: [
                { label: '关联文件', action: 'LINK_FILE', icon: '🔗' },
                { label: '邀请协作', action: 'INVITE_COLLAB', icon: '👥' }
            ]
        },

        // ==================== 阶段3: 进阶 ====================

        PRIVATE_SPACE_REQUESTED: {
            title: '私人空间申请已提交',
            message: '等待团队所有者审核。同时，您可以创建笔记本记录学习笔记',
            icon: '⏳',
            condition: (ctx) => ctx.privateSpaceStatus === 'pending',
            actions: [
                { label: '创建学习笔记', action: 'CREATE_NOTEBOOK', icon: '📓' },
                { label: '查看申请状态', action: 'VIEW_REQUEST_STATUS', icon: '📊' }
            ]
        },

        QUOTA_WARNING: {
            title: '存储空间即将用尽',
            message: '您的空间配额已使用超过80%，请及时清理或申请扩容',
            icon: '⚠️',
            condition: (ctx) => ctx.quotaUsage > 0.8,
            actions: [
                { label: '查看回收站', action: 'OPEN_TRASH', icon: '🗑️' },
                { label: '申请扩容', action: 'REQUEST_QUOTA', icon: '📈' },
                { label: '了解配额', action: 'LEARN_QUOTA', icon: '💡' }
            ]
        },

        // ==================== 阶段4: 专家 ====================

        CROSS_TEAM_COLLABORATION: {
            title: '跨团队协作已建立',
            message: '您现在可以跨团队共享文件和笔记，探索高级协作功能',
            icon: '🔄',
            condition: (ctx) => ctx.crossTeamSpaces > 0,
            actions: [
                { label: '创建共享笔记本', action: 'CREATE_SHARED_NOTEBOOK', icon: '📓' },
                { label: '设置跨团队工作流', action: 'CREATE_CROSS_TEAM_WORKFLOW', icon: '🔄' },
                { label: '查看协作分析', action: 'VIEW_COLLAB_ANALYTICS', icon: '📊' }
            ]
        }
    })

    console.log('[GuidanceBoot] 10 guidance events registered')

    // 设置全局调试模式（控制台输入 window.guidance.debug = true 开启）
    if (window.guidance) {
        window.guidance.debug = false
    }
}

/**
 * 触发引导事件的便捷函数
 * @param {string} event - 事件名称
 * @param {Object} context - 上下文数据
 */
window.triggerGuidance = function(event, context = {}) {
    if (window.guidance) {
        return window.guidance.trigger(event, context)
    }
    console.error('[GuidanceBoot] GuidanceEngine not available')
    return false
}

/**
 * 重置所有引导状态
 */
window.resetGuidance = function() {
    if (window.guidance) {
        window.guidance.resetAll()
        console.log('[GuidanceBoot] All guidance state reset')
    }
}

/**
 * 查看引导状态
 */
window.guidanceStatus = function() {
    if (window.guidance) {
        console.table(window.guidance.getAllStatus())
    }
}
