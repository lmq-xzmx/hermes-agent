/**
 * 引导弹窗组件
 *
 * 用于显示生命周期约束违反时的用户引导
 */
class GuidanceModal {
    constructor(options = {}) {
        this.title = options.title || '操作受限'
        this.message = options.message || ''
        this.icon = options.icon || '⚠️'
        this.guidance = options.guidance || {}
        this.actions = options.actions || []
        this.onAction = options.onAction || (() => {})
        this.onDismiss = options.onDismiss || (() => {})
        this.onDismissType = options.onDismissType || null  // 新增：不再显示回调
        this.eventType = options.eventType || ''  // 新增：事件类型
        this.modalId = 'guidance-modal-' + Date.now()
    }

    show() {
        // 支持单action或多actions
        const actions = this.actions || (this.guidance && this.guidance.label ? [this.guidance] : [])
        const primaryAction = actions.find(a => a.primary) || actions[0]
        const secondaryActions = actions.filter(a => a !== primaryAction)

        const actionsHtml = primaryAction ? `
            <button class="guidance-action primary" data-action="${primaryAction.action || primaryAction.label}">
                ${primaryAction.icon ? `<span class="action-icon">${primaryAction.icon}</span>` : ''}
                <span class="action-label">${primaryAction.label}</span>
            </button>
        ` : ''

        const secondaryHtml = secondaryActions.length > 0 ? secondaryActions.map(a => `
            <button class="guidance-action secondary" data-action="${a.action || a.label}">
                ${a.icon ? `<span class="action-icon">${a.icon}</span>` : ''}
                <span class="action-label">${a.label}</span>
            </button>
        `).join('') : ''

        // 不再显示复选框（当提供 onDismissType 时显示）
        const dismissCheckboxHtml = this.onDismissType ? `
            <label class="guidance-dismiss-checkbox">
                <input type="checkbox" id="dismiss-checkbox">
                <span>不再显示此类提示</span>
            </label>
        ` : ''

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
                        <div class="guidance-details" style="display:none;"></div>
                    </div>
                    <div class="guidance-footer">
                        ${actionsHtml}
                        ${secondaryHtml}
                        ${dismissCheckboxHtml}
                        ${secondaryActions.length > 0 ? `
                            <button class="guidance-dismiss">
                                取消
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `

        // 插入到 body
        document.body.insertAdjacentHTML('beforeend', modalHtml)

        // 绑定事件
        this.bindEvents()

        // 显示动画
        requestAnimationFrame(() => {
            const modal = document.getElementById(this.modalId)
            if (modal) modal.classList.add('show')
        })
    }

    bindEvents() {
        const modal = document.getElementById(this.modalId)
        if (!modal) return

        const overlay = modal.querySelector('.guidance-overlay')
        const closeBtn = modal.querySelector('.guidance-close')
        const dismissBtn = modal.querySelector('.guidance-dismiss')
        const dismissCheckbox = modal.querySelector('#dismiss-checkbox')

        // 支持多个 action 按钮
        const actionBtns = modal.querySelectorAll('.guidance-action')

        // 不再显示复选框事件
        if (dismissCheckbox && this.onDismissType) {
            dismissCheckbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this._dismissForever = true
                }
            })
        }

        overlay.addEventListener('click', () => this._handleHide())
        closeBtn.addEventListener('click', () => this._handleHide())

        if (dismissBtn) {
            dismissBtn.addEventListener('click', () => this._handleHide())
        }

        actionBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.dataset.action
                this._handleHide()
                this.onAction(action)
            })
        })

        // ESC 键关闭
        this._escHandler = (e) => {
            if (e.key === 'Escape' && document.getElementById(this.modalId)) {
                this._handleHide()
            }
        }
        document.addEventListener('keydown', this._escHandler)
    }

    _handleHide() {
        // 如果用户勾选了"不再显示"
        if (this._dismissForever && this.onDismissType) {
            this.onDismissType()
        }
        this.hide()
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

// 导出以支持模块化使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GuidanceModal
}
