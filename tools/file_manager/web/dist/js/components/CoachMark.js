/**
 * CoachMark - 悬浮提示组件
 *
 * 用于在工作流引导中指向特定 UI 元素
 */
class CoachMark {
    constructor(options = {}) {
        this.target = options.target || null
        this.title = options.title || ''
        this.text = options.text || ''
        this.position = options.position || 'bottom' // top, bottom, left, right
        this.onNext = options.onNext || null
        this.onPrev = options.onPrev || null
        this.onDismiss = options.onDismiss || null
        this.step = options.step || 0
        this.totalSteps = options.totalSteps || 1
        this.markId = 'coach-mark-' + Date.now()
        this.arrowSize = 12
    }

    show() {
        const targetEl = typeof this.target === 'string'
            ? document.querySelector(this.target)
            : this.target

        if (!targetEl) {
            console.warn('[CoachMark] Target element not found:', this.target)
            return
        }

        const rect = targetEl.getBoundingClientRect()
        const markHtml = this.createMarkHtml(rect)

        document.body.insertAdjacentHTML('beforeend', markHtml)
        this.markEl = document.getElementById(this.markId)

        requestAnimationFrame(() => {
            if (this.markEl) this.markEl.classList.add('show')
        })

        // 监听窗口resize/scroll以保持位置
        this._resizeHandler = () => {
            if (this.markEl) {
                const newRect = targetEl.getBoundingClientRect()
                this.updatePosition(newRect)
            }
        }
        window.addEventListener('resize', this._resizeHandler)
        window.addEventListener('scroll', this._resizeHandler, true)
    }

    createMarkHtml(rect) {
        const { top, left, width, height } = rect
        const pos = this.calculatePosition(top, left, width, height)

        return `
            <div class="coach-mark" id="${this.markId}">
                <div class="coach-spotlight" style="
                    top: ${pos.spotlightTop}px;
                    left: ${pos.spotlightLeft}px;
                    width: ${pos.spotlightWidth}px;
                    height: ${pos.spotlightHeight}px;
                "></div>
                <div class="coach-content coach-${this.position}" style="
                    top: ${pos.contentTop}px;
                    left: ${pos.contentLeft}px;
                ">
                    ${this.title ? `<div class="coach-title">${this.escapeHtml(this.title)}</div>` : ''}
                    <div class="coach-text">${this.escapeHtml(this.text)}</div>
                    <div class="coach-footer">
                        ${this.totalSteps > 1 ? `<span class="coach-step">${this.step + 1}/${this.totalSteps}</span>` : ''}
                        <div class="coach-actions">
                            ${this.onPrev && this.step > 0 ? '<button class="coach-btn coach-prev">上一步</button>' : ''}
                            ${this.onNext ? '<button class="coach-btn coach-next">下一步</button>' : '<button class="coach-btn coach-close">关闭</button>'}
                        </div>
                    </div>
                    <div class="coach-arrow coach-arrow-${this.position}" style="
                        ${this.position === 'bottom' ? `top: -${this.arrowSize}px; left: 50%; transform: translateX(-50%);` : ''}
                        ${this.position === 'top' ? `bottom: -${this.arrowSize}px; left: 50%; transform: translateX(-50%);` : ''}
                        ${this.position === 'left' ? `right: -${this.arrowSize}px; top: 50%; transform: translateY(-50%);` : ''}
                        ${this.position === 'right' ? `left: -${this.arrowSize}px; top: 50%; transform: translateY(-50%);` : ''}
                    "></div>
                </div>
            </div>
        `
    }

    calculatePosition(top, left, width, height) {
        const gap = 8
        const contentWidth = 280
        const contentHeight = 120

        let spotlightTop = top - gap
        let spotlightLeft = left - gap
        let spotlightWidth = width + gap * 2
        let spotlightHeight = height + gap * 2
        let contentTop, contentLeft

        switch (this.position) {
            case 'bottom':
                contentTop = top + height + gap * 2 + this.arrowSize
                contentLeft = left + width / 2 - contentWidth / 2
                break
            case 'top':
                contentTop = top - gap * 2 - contentHeight - this.arrowSize
                contentLeft = left + width / 2 - contentWidth / 2
                break
            case 'left':
                contentTop = top + height / 2 - contentHeight / 2
                contentLeft = left - gap * 2 - contentWidth - this.arrowSize
                break
            case 'right':
                contentTop = top + height / 2 - contentHeight / 2
                contentLeft = left + width + gap * 2 + this.arrowSize
                break
            default:
                contentTop = top + height + gap * 2
                contentLeft = left
        }

        // 边界检测
        if (contentLeft < 10) contentLeft = 10
        if (contentLeft + contentWidth > window.innerWidth - 10) {
            contentLeft = window.innerWidth - contentWidth - 10
        }
        if (contentTop < 10) contentTop = 10
        if (contentTop + contentHeight > window.innerHeight - 10) {
            contentTop = window.innerHeight - contentHeight - 10
        }

        return { spotlightTop, spotlightLeft, spotlightWidth, spotlightHeight, contentTop, contentLeft }
    }

    updatePosition(rect) {
        const pos = this.calculatePosition(rect.top, rect.left, rect.width, rect.height)
        const spotlight = this.markEl.querySelector('.coach-spotlight')
        const content = this.markEl.querySelector('.coach-content')

        if (spotlight) {
            spotlight.style.top = pos.spotlightTop + 'px'
            spotlight.style.left = pos.spotlightLeft + 'px'
            spotlight.style.width = pos.spotlightWidth + 'px'
            spotlight.style.height = pos.spotlightHeight + 'px'
        }
        if (content) {
            content.style.top = pos.contentTop + 'px'
            content.style.left = pos.contentLeft + 'px'
        }
    }

    hide() {
        window.removeEventListener('resize', this._resizeHandler)
        window.removeEventListener('scroll', this._resizeHandler, true)

        if (this.markEl) {
            this.markEl.classList.remove('show')
            setTimeout(() => {
                if (this.markEl) {
                    this.markEl.remove()
                    this.markEl = null
                }
            }, 200)
        }
    }

    next() {
        if (this.onNext) {
            const result = this.onNext(this.step)
            if (result === false) {
                this.hide()
            }
        } else {
            this.hide()
        }
    }

    prev() {
        if (this.onPrev) {
            this.onPrev(this.step)
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div')
        div.textContent = text
        return div.innerHTML
    }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CoachMark
}
