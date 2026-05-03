/**
 * GuidanceEngine - 引导引擎
 *
 * 基于事件的新手引导系统核心引擎
 * 负责事件注册、引导触发、状态持久化
 */
class GuidanceEngine {
    constructor(options = {}) {
        this.debug = options.debug ?? false
        this.listeners = new Map()
        this.storagePrefix = 'hermes_guidance_'
        this.modalComponent = options.modalComponent || GuidanceModal
        this.coachMarkComponent = options.coachMarkComponent || null
    }

    // ==================== 事件注册 ====================

    /**
     * 注册引导事件
     * @param {string} event - 事件名称
     * @param {Object} config - 事件配置
     */
    on(event, config) {
        if (typeof config === 'function') {
            config = { handler: config }
        }
        this.listeners.set(event, {
            title: config.title || event,
            message: config.message || '',
            icon: config.icon || '🎯',
            actions: config.actions || [],
            condition: config.condition || (() => true),
            handler: config.handler || (() => {}),
            coachMark: config.coachMark || null,
            once: config.once ?? false,
            dismissed: false
        })
        this.log(`Registered event: ${event}`)
        return this
    }

    /**
     * 批量注册事件
     * @param {Object} events - 事件配置对象
     */
    register(events) {
        Object.entries(events).forEach(([event, config]) => {
            this.on(event, config)
        })
        return this
    }

    // ==================== 引导触发 ====================

    /**
     * 触发引导
     * @param {string} event - 事件名称
     * @param {Object} context - 上下文数据
     */
    trigger(event, context = {}) {
        const handler = this.listeners.get(event)
        if (!handler) {
            this.log(`Event not registered: ${event}`)
            return false
        }

        // 检查是否已忽略
        if (this.isDismissed(event)) {
            this.log(`Event dismissed: ${event}`)
            return false
        }

        // 检查是否已完成（针对 once 事件）
        if (handler.once && this.isCompleted(event)) {
            this.log(`Event already completed: ${event}`)
            return false
        }

        // 检查条件
        try {
            if (!handler.condition(context)) {
                this.log(`Condition not met for: ${event}`)
                return false
            }
        } catch (e) {
            this.log(`Condition error for ${event}: ${e.message}`)
            return false
        }

        // 记录显示次数
        this.incrementShowCount(event)

        // 构建引导配置
        const config = {
            title: handler.title,
            message: handler.message,
            icon: handler.icon,
            actions: handler.actions.map(a => ({
                label: a.label,
                icon: a.icon,
                action: a.action
            })),
            onAction: (action) => {
                this.log(`Action triggered: ${action}`)
                const actionConfig = handler.actions.find(a => a.action === action)
                if (actionConfig && actionConfig.handler) {
                    actionConfig.handler(context)
                } else if (handler.handler) {
                    handler.handler(action, context)
                }
            },
            onDismiss: () => {
                this.dismiss(event)
            }
        }

        // 显示引导弹窗或 Coach Mark
        if (handler.coachMark) {
            this.showCoachMark(handler.coachMark, context)
        } else {
            this.showGuidanceModal(config)
        }

        return true
    }

    /**
     * 显示引导弹窗
     */
    showGuidanceModal(config) {
        const modal = new this.modalComponent({
            title: config.title,
            message: config.message,
            icon: config.icon,
            actions: config.actions,
            onAction: config.onAction,
            onDismiss: config.onDismiss
        })
        modal.show()
        return modal
    }

    /**
     * 显示 Coach Mark
     */
    showCoachMark(coachConfig, context) {
        if (!this.coachMarkComponent) {
            console.warn('CoachMark component not loaded')
            return
        }
        const coach = new this.coachMarkComponent({
            ...coachConfig,
            onNext: coachConfig.onNext,
            onDismiss: () => {
                this.dismissCoachMark()
                if (context.onDismiss) context.onDismiss()
            }
        })
        coach.show()
    }

    dismissCoachMark() {
        if (this._currentCoach) {
            this._currentCoach.hide()
            this._currentCoach = null
        }
    }

    // ==================== 状态管理 ====================

    /**
     * 获取存储键
     */
    storageKey(event, suffix = '') {
        return `${this.storagePrefix}${event}_${suffix}`.trim()
    }

    /**
     * 检查事件是否已忽略
     */
    isDismissed(event) {
        const dismissed = localStorage.getItem(this.storageKey(event, 'dismissed'))
        if (!dismissed) return false

        // 检查是否在有效期外（可选的过期机制）
        const dismissedAt = parseInt(dismissed, 10)
        const dayMs = 24 * 60 * 60 * 1000
        const weekAgo = Date.now() - (7 * dayMs)

        return dismissedAt > weekAgo
    }

    /**
     * 忽略引导（不 再显示）
     */
    dismiss(event) {
        localStorage.setItem(this.storageKey(event, 'dismissed'), Date.now().toString())
        this.log(`Dismissed: ${event}`)
    }

    /**
     * 重置忽略状态
     */
    resetDismiss(event) {
        localStorage.removeItem(this.storageKey(event, 'dismissed'))
    }

    /**
     * 检查事件是否已完成
     */
    isCompleted(event) {
        return localStorage.getItem(this.storageKey(event, 'completed')) === 'true'
    }

    /**
     * 标记事件为已完成
     */
    complete(event) {
        localStorage.setItem(this.storageKey(event, 'completed'), 'true')
        this.log(`Completed: ${event}`)
    }

    /**
     * 重置完成状态
     */
    resetComplete(event) {
        localStorage.removeItem(this.storageKey(event, 'completed'))
    }

    /**
     * 增加显示次数
     */
    incrementShowCount(event) {
        const key = this.storageKey(event, 'show_count')
        const count = parseInt(localStorage.getItem(key) || '0', 10)
        localStorage.setItem(key, (count + 1).toString())
    }

    /**
     * 获取显示次数
     */
    getShowCount(event) {
        return parseInt(localStorage.getItem(this.storageKey(event, 'show_count')) || '0', 10)
    }

    /**
     * 获取事件状态
     */
    getEventStatus(event) {
        return {
            dismissed: this.isDismissed(event),
            completed: this.isCompleted(event),
            showCount: this.getShowCount(event),
            registered: this.listeners.has(event)
        }
    }

    // ==================== 工具方法 ====================

    /**
     * 重置所有引导状态
     */
    resetAll() {
        const prefix = this.storagePrefix
        Object.keys(localStorage)
            .filter(key => key.startsWith(prefix))
            .forEach(key => localStorage.removeItem(key))
        this.log('All guidance state reset')
    }

    /**
     * 获取所有事件状态
     */
    getAllStatus() {
        const status = {}
        this.listeners.forEach((_, event) => {
            status[event] = this.getEventStatus(event)
        })
        return status
    }

    /**
     * 调试日志
     */
    log(...args) {
        if (this.debug) {
            console.log('[GuidanceEngine]', ...args)
        }
    }
}

// 导出单例
window.guidance = new GuidanceEngine({ debug: false })
