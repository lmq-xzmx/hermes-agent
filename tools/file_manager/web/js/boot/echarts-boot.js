/**
 * echarts-boot.js - ECharts 主题注册
 *
 * 在 DOM 加载完成后注册 admin-dark 主题
 */

// 等待 DOM 加载完成
document.addEventListener('DOMContentLoaded', () => {
    registerAdminTheme()
})

/**
 * 注册 Admin Dashboard ECharts 暗色主题
 */
function registerAdminTheme() {
    // 检查是否已加载 ECharts
    if (typeof echarts === 'undefined') {
        console.warn('[EChartsBoot] ECharts not found, retrying...')
        setTimeout(registerAdminTheme, 100)
        return
    }

    // adminChartTheme 配置
    const adminChartTheme = {
        color: [
            '#58a6ff', '#3fb950', '#d29922', '#f85149',
            '#a371f7', '#f778ba', '#79c0ff', '#7ee787'
        ],
        backgroundColor: 'transparent',
        textStyle: {
            color: '#8b949e',
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif'
        },
        title: {
            textStyle: { color: '#e6edf3', fontSize: 16, fontWeight: 600 },
            subtextStyle: { color: '#8b949e', fontSize: 12 }
        },
        legend: {
            textStyle: { color: '#8b949e' },
            inactiveColor: '#484f58'
        },
        tooltip: {
            backgroundColor: 'rgba(22, 27, 34, 0.95)',
            borderColor: '#30363d',
            borderWidth: 1,
            textStyle: { color: '#e6edf3', fontSize: 13 }
        },
        grid: {
            borderColor: '#30363d',
            left: 12, right: 12, top: 40, bottom: 24,
            containLabel: true
        },
        categoryAxis: {
            axisLine: { lineStyle: { color: '#30363d' } },
            axisTick: { lineStyle: { color: '#30363d' } },
            axisLabel: { color: '#8b949e', fontSize: 11 },
            splitLine: { show: false }
        },
        valueAxis: {
            axisLine: { show: false },
            axisTick: { show: false },
            axisLabel: { color: '#8b949e', fontSize: 11 },
            splitLine: { lineStyle: { color: '#21262d' } }
        },
        line: {
            smooth: true, symbol: 'circle', symbolSize: 6,
            lineStyle: { width: 2 }
        },
        pie: {
            itemStyle: { borderWidth: 2, borderColor: '#161b22' }
        },
        sankey: {
            node: {
                label: { color: '#e6edf3', fontSize: 12 }
            },
            link: {
                lineStyle: { color: 'gradient', opacity: 0.4 }
            }
        }
    }

    // 注册主题
    echarts.registerTheme('admin-dark', adminChartTheme)
    console.log('[EChartsBoot] admin-dark theme registered')
}
