/**
 * WorkflowTour - 工作流创建引导 Tour
 *
 * 4 步骤引导：
 * 1. 输入工作流名称和描述
 * 2. 添加执行步骤
 * 3. 设置共享选项
 * 4. 从模板选择（动态加载后端模板）
 */
class WorkflowTour {
    constructor() {
        this.templates = []
        this.loadingTemplates = false
        this.currentStep = 0
        this.tourId = 'workflow-tour-' + Date.now()
    }

    getSteps() {
        const templateList = this.templates.length > 0
            ? this.templates.slice(0, 3).map(t => `• ${t.name}`).join('\n  ')
            : '• 文件归档流程\n• 审批流程\n• 数据备份'

        return [
            {
                target: '#wf_name',
                position: 'bottom',
                content: '⚙️ 输入工作流名称，如"文件审批流程"或"自动备份"'
            },
            {
                target: '#wf_tags',
                position: 'bottom',
                content: '🏷 添加标签方便分类，如"审批"、"自动化"'
            },
            {
                target: '#wfStepsSection',
                position: 'top',
                content: '📋 点击"+ 添加步骤"添加工作流命令，如 shell 命令或 API 调用'
            },
            {
                target: '#wf_shared',
                position: 'right',
                content: `👥 勾选"团队共享"可以让空间成员使用此工作流\n\n📋 可用模板：\n  ${templateList}`
            }
        ]
    }

    start() {
        this.currentStep = 0
        this.loadTemplates().then(() => {
            this.showStep(0)
        })
    }

    async loadTemplates() {
        if (this.loadingTemplates) return
        this.loadingTemplates = true

        try {
            // 从后端获取工作流模板列表
            const resp = await fetch('/api/v1/workflows/templates')
            if (resp.ok) {
                const data = await resp.json()
                this.templates = data.templates || data.workflows || []
            } else {
                console.warn('[WorkflowTour] Failed to load templates:', resp.status)
                this.templates = []
            }
        } catch (e) {
            console.warn('[WorkflowTour] Error loading templates:', e)
            this.templates = []
        } finally {
            this.loadingTemplates = false
        }
    }

    showStep(index) {
        const steps = this.getSteps()
        const step = steps[index]
        if (!step) {
            this.end()
            return
        }

        const targetEl = document.querySelector(step.target)
        if (!targetEl) {
            console.warn('[WorkflowTour] Target not found:', step.target)
            this.next()
            return
        }

        if (this._currentCoach) {
            this._currentCoach.hide()
        }

        const rect = targetEl.getBoundingClientRect()
        const pos = this.calculatePosition(rect, step.position)

        const html = `
            <div class="workflow-tour" id="${this.tourId}">
                <div class="tour-spotlight" style="
                    top: ${pos.spotlightTop}px;
                    left: ${pos.spotlightLeft}px;
                    width: ${pos.spotlightWidth}px;
                    height: ${pos.spotlightHeight}px;
                "></div>
                <div class="tour-tooltip" style="top: ${pos.contentTop}px; left: ${pos.contentLeft}px;">
                    <div class="tour-header">
                        <span class="tour-step-badge">步骤 ${index + 1}/${steps.length}</span>
                        <button class="tour-close" onclick="window._workflowTour.end()">×</button>
                    </div>
                    <p class="tour-text">${step.content}</p>
                    <div class="tour-footer">
                        ${index > 0 ? '<button class="tour-btn secondary" onclick="window._workflowTour.prev()">← 上一步</button>' : ''}
                        <button class="tour-btn primary" onclick="window._workflowTour.next()">
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

        this._resizeHandler = () => this.showStep(index)
        window.addEventListener('resize', this._resizeHandler)
    }

    calculatePosition(rect, position) {
        const gap = 8
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
        window._workflowTour = null
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
window.startWorkflowTour = function() {
    if (window._workflowTour) {
        window._workflowTour.end()
    }
    window._workflowTour = new WorkflowTour()
    window._workflowTour.onComplete = () => {
        console.log('[WorkflowTour] Guide completed')
    }
    window._workflowTour.start()
}

window.endWorkflowTour = function() {
    if (window._workflowTour) {
        window._workflowTour.end()
    }
}
