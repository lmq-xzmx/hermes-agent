/**
 * NotebookTour - 笔记本创建引导 Tour
 *
 * 4 步骤引导：
 * 1. 输入名称和标签
 * 2. 编写初始内容
 * 3. 设置共享选项
 * 4. 关联到空间（动态加载空间列表）
 */
class NotebookTour {
    constructor() {
        this.spaces = []
        this.loadingSpaces = false
        this.currentStep = 0
        this.coach = null
        this.tourId = 'notebook-tour-' + Date.now()
    }

    getSteps() {
        const spaceList = this.spaces.length > 0
            ? this.spaces.slice(0, 3).map(s => `• ${s.name}`).join('\n  ')
            : '• 项目空间\n• 会议记录\n• 团队知识库'

        return [
            {
                target: '#nb_name',
                position: 'bottom',
                content: '📓 输入笔记本名称，如"项目需求文档"或"会议纪要"'
            },
            {
                target: '#nb_tags',
                position: 'bottom',
                content: '🏷 添加标签方便分类管理，如"项目"、"会议"、"教程"'
            },
            {
                target: '#nb_content',
                position: 'top',
                content: '✍️ 使用 Markdown 编写内容，支持标题、列表、代码高亮'
            },
            {
                target: '#nb_shared',
                position: 'right',
                content: `👥 勾选"团队共享"可以让空间成员协作编辑\n\n📁 可关联空间：\n  ${spaceList}`
            }
        ]
    }

    start() {
        this.currentStep = 0
        this.loadSpaces().then(() => {
            this.showStep(0)
        })
    }

    async loadSpaces() {
        if (this.loadingSpaces) return
        this.loadingSpaces = true

        try {
            // 从后端获取用户可用的空间列表
            const resp = await fetch('/api/v1/spaces')
            if (resp.ok) {
                const data = await resp.json()
                this.spaces = data.spaces || data.data || []
            } else {
                console.warn('[NotebookTour] Failed to load spaces:', resp.status)
                this.spaces = []
            }
        } catch (e) {
            console.warn('[NotebookTour] Error loading spaces:', e)
            this.spaces = []
        } finally {
            this.loadingSpaces = false
        }
    }

    showStep(index) {
        const steps = this.getSteps()
        const step = steps[index]
        if (!step) {
            this.end()
            return
        }

        // 等待目标元素出现
        const targetEl = document.querySelector(step.target)
        if (!targetEl) {
            console.warn('[NotebookTour] Target not found:', step.target)
            this.next()
            return
        }

        // 关闭之前的 coach
        if (this.coach) {
            this.coach.hide()
        }

        // 计算位置
        const rect = targetEl.getBoundingClientRect()
        const pos = this.calculatePosition(rect, step.position)

        // 创建引导 HTML
        const html = `
            <div class="notebook-tour" id="${this.tourId}">
                <div class="tour-spotlight" style="
                    top: ${pos.spotlightTop}px;
                    left: ${pos.spotlightLeft}px;
                    width: ${pos.spotlightWidth}px;
                    height: ${pos.spotlightHeight}px;
                "></div>
                <div class="tour-tooltip" style="top: ${pos.contentTop}px; left: ${pos.contentLeft}px;">
                    <div class="tour-header">
                        <span class="tour-step-badge">步骤 ${index + 1}/${steps.length}</span>
                        <button class="tour-close" onclick="window._notebookTour.end()">×</button>
                    </div>
                    <p class="tour-text">${step.content}</p>
                    <div class="tour-footer">
                        ${index > 0 ? '<button class="tour-btn secondary" onclick="window._notebookTour.prev()">← 上一步</button>' : ''}
                        <button class="tour-btn primary" onclick="window._notebookTour.next()">
                            ${index === steps.length - 1 ? '完成' : '下一步 →'}
                        </button>
                    </div>
                    <div class="tour-progress">
                        ${steps.map((_, i) => `<span class="tour-dot ${i <= index ? 'active' : ''}"></span>`).join('')}
                    </div>
                </div>
            </div>
        `

        document.body.insertAdjacentHTML('beforeend', html)

        // 监听 resize
        this._resizeHandler = () => this.showStep(index)
        window.addEventListener('resize', this._resizeHandler)
    }

    calculatePosition(rect, position) {
        const gap = 8
        const padding = 12
        const tooltipWidth = 280
        const tooltipHeight = 160

        const spotlightTop = rect.top - gap
        const spotlightLeft = rect.left - gap
        const spotlightWidth = rect.width + gap * 2
        const spotlightHeight = rect.height + gap * 2

        let contentTop, contentLeft

        switch (position) {
            case 'bottom':
                contentTop = rect.bottom + gap * 2 + 12
                contentLeft = rect.left + rect.width / 2 - tooltipWidth / 2
                break
            case 'top':
                contentTop = rect.top - gap * 2 - tooltipHeight - 12
                contentLeft = rect.left + rect.width / 2 - tooltipWidth / 2
                break
            case 'left':
                contentTop = rect.top + rect.height / 2 - tooltipHeight / 2
                contentLeft = rect.left - gap * 2 - tooltipWidth - 12
                break
            case 'right':
                contentTop = rect.top + rect.height / 2 - tooltipHeight / 2
                contentLeft = rect.right + gap * 2 + 12
                break
            default:
                contentTop = rect.bottom + gap * 2
                contentLeft = rect.left
        }

        // 边界检测
        if (contentLeft < 10) contentLeft = 10
        if (contentLeft + tooltipWidth > window.innerWidth - 10) {
            contentLeft = window.innerWidth - tooltipWidth - 10
        }
        if (contentTop < 10) contentTop = 10
        if (contentTop + tooltipHeight > window.innerHeight - 10) {
            contentTop = window.innerHeight - tooltipHeight - 10
        }

        return { spotlightTop, spotlightLeft, spotlightWidth, spotlightHeight, contentTop, contentLeft }
    }

    next() {
        this.currentStep++
        if (this.currentStep >= this.getSteps().length) {
            this.end()
            return
        }
        this.clear()
        this.showStep(this.currentStep)
    }

    prev() {
        if (this.currentStep > 0) {
            this.currentStep--
            this.clear()
            this.showStep(this.currentStep)
        }
    }

    end() {
        this.clear()
        window._notebookTour = null
        // 触发完成事件
        if (this.onComplete) {
            this.onComplete()
        }
    }

    clear() {
        window.removeEventListener('resize', this._resizeHandler)
        const el = document.getElementById(this.tourId)
        if (el) el.remove()
    }
}

// 全局实例管理
window.startNotebookTour = function() {
    if (window._notebookTour) {
        window._notebookTour.end()
    }
    window._notebookTour = new NotebookTour()
    window._notebookTour.onComplete = () => {
        console.log('[NotebookTour] Guide completed')
    }
    window._notebookTour.start()
}

window.endNotebookTour = function() {
    if (window._notebookTour) {
        window._notebookTour.end()
    }
}
