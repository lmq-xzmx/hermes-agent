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
        this.onAction = options.onAction || (() => {})
        this.onDismiss = options.onDismiss || (() => {})
        this.modalId = 'guidance-modal-' + Date.now()
    }

    show() {
        // 创建模态框
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
                        <button class="guidance-action primary">
                            ${this.guidance.icon ? `<span class="action-icon">${this.guidance.icon}</span>` : ''}
                            <span class="action-label">${this.guidance.label || '确定'}</span>
                        </button>
                        <button class="guidance-dismiss">
                            取消
                        </button>
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
        const actionBtn = modal.querySelector('.guidance-action')
        const dismissBtn = modal.querySelector('.guidance-dismiss')

        overlay.addEventListener('click', () => this.hide())
        closeBtn.addEventListener('click', () => this.hide())
        dismissBtn.addEventListener('click', () => this.hide())
        actionBtn.addEventListener('click', () => {
            this.hide()
            this.onAction()
        })

        // ESC 键关闭
        this._escHandler = (e) => {
            if (e.key === 'Escape' && document.getElementById(this.modalId)) {
                this.hide()
            }
        }
        document.addEventListener('keydown', this._escHandler)
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
