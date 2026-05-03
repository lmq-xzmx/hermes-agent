/**
 * 生命周期操作拦截器
 *
 * 在执行危险操作前检查约束条件，
 * 违规时显示引导弹窗而非直接拒绝
 *
 * 配置来源: /api/v1/lifecycle/config (后端 config/lifecycle_config.yaml)
 */
class LifecycleInterceptor {
    constructor(options = {}) {
        this.enabled = options.enabled ?? true
        this.debug = options.debug ?? false
        this.constraints = new Map()
        this.guidanceCallbacks = new Map()
        this._configLoaded = false

        this.init()
    }

    async init() {
        await this.loadConfig()
        this.registerDefaultConstraints()
        this.setupGlobalHandlers()
    }

    async loadConfig() {
        try {
            const response = await fetch('/api/v1/lifecycle/config')
            if (response.ok) {
                const config = await response.json()
                this._applyConfig(config)
                this._configLoaded = true
                this.debug && console.log('[Lifecycle] Config loaded from server')
            }
        } catch (e) {
            console.warn('[Lifecycle] Failed to load config, using hardcoded rules:', e)
        }
    }

    _applyConfig(config) {
        const rules = config.rules || {}
        for (const [action, ruleList] of Object.entries(rules)) {
            for (const rule of ruleList) {
                this.registerConstraint(action, {
                    code: rule.code,
                    check: (context) => this._evaluateCheck(rule, context),
                    error: {
                        title: this._getErrorTitle(action),
                        message: rule.error_template,
                        icon: rule.guidance?.icon || '⚠️'
                    },
                    guidance: {
                        label: rule.guidance?.label || '确定',
                        icon: rule.guidance?.icon || '',
                        path: rule.guidance?.path,
                        action: rule.guidance?.action
                    },
                    priority: rule.priority || 0
                })
            }
        }
    }

    _evaluateCheck(rule, context) {
        const code = rule.code
        const desc = (rule.description || '').toLowerCase()

        // Map rule codes to context field checks
        const checks = {
            'NOT_SPACE_MEMBER': () => context.isMember,
            'QUOTA_SUFFICIENT': () => context.hasQuota,
            'QUOTA_RESERVED': () => context.quotaReserved === 0 || context.canOverride,
            'QUOTA_EXCEEDED': () => context.sufficientQuota,
            'NO_AVAILABLE_POOL': () => context.hasAvailablePool,
            'STORAGE_POOL_IN_USE': () => context.teamCount === 0,
            'POOL_TEAMS_MIGRATING': () => context.teamMigratingCount === 0,
            'SPACE_NO_MEMBERS': () => context.memberCount === 0,
            'SPACE_HAS_PENDING_REQUESTS': () => context.pendingRequestCount === 0,
            'NOT_SPACE_OWNER': () => context.isOwner,
            'MEMBER_RECENTLY_REMOVED': () => !context.wasRecentlyRemoved,
            'NOT_TEAM_OWNER': () => context.isOwner,
            'CREDENTIAL_VALID': () => context.credentialValid,
            'NOT_TEAM_MEMBER': () => context.isTeamMember,
            'NOT_QUOTA_OWNER': () => context.isOwner
        }

        const checkFn = checks[code]
        if (checkFn) {
            const result = checkFn()
            if (!result) {
                return { allowed: false, code }
            }
        }
        return true
    }

    _getErrorTitle(action) {
        const titles = {
            'upload_file': '无法上传文件',
            'create_team': '无法创建团队',
            'create_private_space': '无法创建私人空间',
            'delete_pool': '无法删除存储池',
            'delete_space': '无法删除空间',
            'delete_team': '无法删除团队',
            'invite_member': '无法邀请成员',
            'check_quota': '配额不足',
            'update_quota': '无法修改配额',
            'join_team': '无法加入团队'
        }
        return titles[action] || '操作受限'
    }

    registerDefaultConstraints() {
        // 如果已从后端加载配置，跳过硬编码规则
        if (this._configLoaded) return

        // 上传文件约束
        this.registerConstraint('upload_file', {
            check: async (context) => {
                if (context.quotaReserved > 0 && !context.canOverride) {
                    return { allowed: false, code: 'QUOTA_RESERVED' }
                }
                return context.isMember && context.hasQuota
            },
            error: {
                title: '无法上传文件',
                message: '您还没有加入任何团队，无法上传文件。请先加入一个团队或创建一个新团队。',
                icon: '📤'
            },
            guidance: {
                label: '加入团队',
                icon: '👥',
                path: '/teams'
            }
        })

        // 创建团队约束
        this.registerConstraint('create_team', {
            check: async (context) => {
                return context.hasAvailablePool
            },
            error: {
                title: '无法创建团队',
                message: '系统暂无可用存储池，无法创建新团队。请联系管理员创建存储池后再试。',
                icon: '👥'
            },
            guidance: {
                label: '联系管理员',
                icon: '📧',
                action: 'showContactAdminModal'
            }
        })

        // 创建私人空间约束
        this.registerConstraint('create_private_space', {
            check: async (context) => {
                return context.isTeamMember
            },
            error: {
                title: '无法创建私人空间',
                message: '只有团队成员才能申请私人空间。',
                icon: '🔒'
            },
            guidance: {
                label: '加入团队',
                icon: '👥',
                path: '/teams'
            }
        })

        // 删除存储池约束
        this.registerConstraint('delete_pool', {
            check: async (context) => {
                if (context.teamMigratingCount > 0) {
                    return { allowed: false, code: 'POOL_TEAMS_MIGRATING' }
                }
                return context.teamCount === 0
            },
            error: {
                title: '无法删除存储池',
                message: '该存储池仍有团队使用，无法删除。请先将团队迁移到其他存储池。',
                icon: '⚠️'
            },
            guidance: {
                label: '查看团队',
                icon: '👥',
                path: '/admin/teams'
            }
        })

        // 删除空间约束
        this.registerConstraint('delete_space', {
            check: async (context) => {
                if (context.pendingRequestCount > 0) {
                    return { allowed: false, code: 'SPACE_HAS_PENDING_REQUESTS' }
                }
                return context.memberCount === 0
            },
            error: {
                title: '无法删除空间',
                message: '该空间仍有成员，无法删除。请先移除所有成员。',
                icon: '👥'
            },
            guidance: {
                label: '查看成员',
                icon: '👥',
                path: '/admin/members'
            }
        })

        // 删除团队约束
        this.registerConstraint('delete_team', {
            check: async (context) => {
                return context.isOwner
            },
            error: {
                title: '无法删除团队',
                message: '只有团队所有者可以删除团队。',
                icon: '👥'
            },
            guidance: {
                label: '联系管理员',
                icon: '📧',
                action: 'showContactAdminModal'
            }
        })

        // 邀请成员约束
        this.registerConstraint('invite_member', {
            check: async (context) => {
                if (context.wasRecentlyRemoved) {
                    return { allowed: false, code: 'MEMBER_RECENTLY_REMOVED' }
                }
                return context.isOwner
            },
            error: {
                title: '无法邀请成员',
                message: '只有空间所有者可以邀请新成员。',
                icon: '👥'
            },
            guidance: {
                label: '联系管理员',
                icon: '📧',
                action: 'showContactAdminModal'
            }
        })

        // 配额检查约束
        this.registerConstraint('check_quota', {
            check: async (context) => {
                return context.sufficientQuota
            },
            error: {
                title: '配额不足',
                message: '存储配额已用尽，无法上传新文件。请清理回收站或联系管理员申请扩容。',
                icon: '💾'
            },
            guidance: {
                label: '查看回收站',
                icon: '🗑️',
                path: '/trash'
            }
        })

        // 更新配额约束
        this.registerConstraint('update_quota', {
            check: async (context) => {
                return context.isOwner
            },
            error: {
                title: '无法修改配额',
                message: '只有空间所有者可以修改配额。',
                icon: '💾'
            },
            guidance: {
                label: '联系管理员',
                icon: '📧',
                action: 'showContactAdminModal'
            }
        })

        // 加入团队约束
        this.registerConstraint('join_team', {
            check: async (context) => {
                return context.credentialValid
            },
            error: {
                title: '无法加入团队',
                message: '邀请码已过期或无效。',
                icon: '🔗'
            },
            guidance: {
                label: '联系管理员',
                icon: '📧',
                action: 'showContactAdminModal'
            }
        })
    }

    /**
     * 注册约束规则
     */
    registerConstraint(action, config) {
        this.constraints.set(action, config)
    }

    /**
     * 注册引导回调
     */
    registerGuidanceCallback(action, callback) {
        this.guidanceCallbacks.set(action, callback)
    }

    /**
     * 执行操作前的约束检查
     */
    async beforeAction(action, context) {
        if (!this.enabled) return { allowed: true }

        const constraint = this.constraints.get(action)
        if (!constraint) {
            this.debug && console.log(`[Lifecycle] No constraint for action: ${action}`)
            return { allowed: true }
        }

        try {
            const result = await constraint.check(context)

            // 处理对象返回格式 { allowed: false, code: 'XXX', ... }
            if (typeof result === 'object' && result !== null) {
                if (result.allowed !== false) {
                    this.debug && console.log(`[Lifecycle] Constraint passed: ${action}`)
                    return { allowed: true }
                }
                // 约束违反，根据 code 返回对应错误
                this.debug && console.log(`[Lifecycle] Constraint violated: ${action}`, result.code)
                return {
                    allowed: false,
                    error: constraint.error,
                    guidance: constraint.guidance
                }
            }

            // 处理布尔返回格式
            if (result) {
                this.debug && console.log(`[Lifecycle] Constraint passed: ${action}`)
                return { allowed: true }
            }

            // 约束违反，显示引导弹窗
            this.debug && console.log(`[Lifecycle] Constraint violated: ${action}`)
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
    showGuidanceModal(config) {
        const modal = new GuidanceModal({
            title: config.error.title,
            message: config.error.message,
            icon: config.error.icon,
            guidance: config.guidance,
            onAction: () => this.executeGuidance(config.guidance),
            onDismiss: () => this.onGuidanceDismissed(config)
        })
        modal.show()
        return modal
    }

    /**
     * 执行引导操作
     */
    executeGuidance(guidance) {
        if (guidance.path) {
            // 导航到指定路径
            if (typeof router !== 'undefined' && router.push) {
                router.push(guidance.path)
            } else if (typeof navigateTo === 'function') {
                navigateTo(guidance.path)
            } else {
                window.location.hash = guidance.path
            }
        } else if (guidance.action) {
            // 执行回调
            const callback = this.guidanceCallbacks.get(guidance.action)
            if (callback) {
                callback()
            }
        }
    }

    /**
     * 引导弹窗关闭后的处理
     */
    onGuidanceDismissed(config) {
        // 可选：记录用户已忽略此引导
        localStorage.setItem(`guidance_dismissed_${config.action}`, Date.now().toString())
    }

    /**
     * 设置全局错误处理
     */
    setupGlobalHandlers() {
        // 拦截 API 错误响应
        window.addEventListener('unhandledrejection', (event) => {
            if (event.reason?.code?.startsWith('LIFECYCLE_') ||
                event.reason?.error?.code?.startsWith('LIFECYCLE_')) {
                event.preventDefault()
                this.handleApiError(event.reason)
            }
        })
    }

    /**
     * 处理 API 错误
     */
    handleApiError(error) {
        if (error.guidance) {
            this.showGuidanceModal({
                error: { title: error.message, message: error.details?.message || error.message },
                guidance: error.guidance
            })
        }
    }
}

// 创建全局单例
window.lifecycleInterceptor = new LifecycleInterceptor({ debug: false })
