/**
 * Admin Dashboard ECharts 统一主题配置
 *
 * 用于所有 Admin 可视化图表的暗色主题适配
 */

export const adminChartTheme = {
  // 调色板
  color: [
    '#58a6ff', // 蓝色 - primary
    '#3fb950', // 绿色 - success
    '#d29922', // 橙色 - warning
    '#f85149', // 红色 - danger
    '#a371f7', // 紫色 - info
    '#f778ba', // 粉色
    '#79c0ff', // 浅蓝
    '#7ee787', // 浅绿
  ],

  // 背景色
  backgroundColor: 'transparent',

  // 文字样式
  textStyle: {
    color: '#8b949e',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif',
  },

  // 标题样式
  title: {
    textStyle: {
      color: '#e6edf3',
      fontSize: 16,
      fontWeight: 600,
    },
    subtextStyle: {
      color: '#8b949e',
      fontSize: 12,
    },
  },

  // 图例样式
  legend: {
    textStyle: {
      color: '#8b949e',
    },
    pageTextStyle: {
      color: '#8b949e',
    },
    inactiveColor: '#484f58',
  },

  // 提示框样式
  tooltip: {
    backgroundColor: 'rgba(22, 27, 34, 0.95)',
    borderColor: '#30363d',
    borderWidth: 1,
    textStyle: {
      color: '#e6edf3',
      fontSize: 13,
    },
    axisPointer: {
      lineStyle: {
        color: '#58a6ff',
        width: 1,
      },
      crossStyle: {
        color: '#58a6ff',
        width: 1,
      },
    },
  },

  // 网格样式
  grid: {
    borderColor: '#30363d',
    left: 12,
    right: 12,
    top: 40,
    bottom: 24,
    containLabel: true,
  },

  // 坐标轴样式
  axis: {
    axisLine: {
      lineStyle: {
        color: '#30363d',
      },
    },
    axisTick: {
      lineStyle: {
        color: '#30363d',
      },
    },
    axisLabel: {
      color: '#8b949e',
      fontSize: 11,
    },
    splitLine: {
      lineStyle: {
        color: '#21262d',
      },
    },
  },

  // 类目轴
  categoryAxis: {
    axisLine: {
      lineStyle: {
        color: '#30363d',
      },
    },
    axisTick: {
      lineStyle: {
        color: '#30363d',
      },
    },
    axisLabel: {
      color: '#8b949e',
      fontSize: 11,
    },
    splitLine: {
      show: false,
    },
  },

  // 数值轴
  valueAxis: {
    axisLine: {
      show: false,
    },
    axisTick: {
      show: false,
    },
    axisLabel: {
      color: '#8b949e',
      fontSize: 11,
    },
    splitLine: {
      lineStyle: {
        color: '#21262d',
      },
    },
  },

  // 柱状图样式
  bar: {
    itemStyle: {
      borderRadius: [4, 4, 0, 0],
    },
  },

  // 饼图样式
  pie: {
    itemStyle: {
      borderWidth: 2,
      borderColor: '#161b22',
    },
  },

  // 折线图样式
  line: {
    smooth: true,
    symbol: 'circle',
    symbolSize: 6,
    lineStyle: {
      width: 2,
    },
    emphasis: {
      lineStyle: {
        width: 3,
      },
    },
  },

  // 桑基图样式
  sankey: {
    node: {
      itemStyle: {
        borderWidth: 0,
      },
      label: {
        color: '#e6edf3',
        fontSize: 12,
      },
    },
    link: {
      lineStyle: {
        color: 'gradient',
        opacity: 0.4,
      },
      emphasis: {
        lineStyle: {
          opacity: 0.6,
        },
      },
    },
  },

  // 热力图样式
  heatmap: {
    label: {
      show: true,
      color: '#e6edf3',
      fontSize: 11,
    },
  },

  // 仪表盘样式
  gauge: {
    axisLine: {
      lineStyle: {
        width: 8,
      },
    },
    axisTick: {
      distance: -12,
      length: 6,
      lineStyle: {
        color: '#30363d',
      },
    },
    splitLine: {
      distance: -12,
      length: 10,
      lineStyle: {
        color: '#30363d',
      },
    },
    axisLabel: {
      color: '#8b949e',
      fontSize: 11,
      distance: 20,
    },
    detail: {
      color: '#e6edf3',
      fontSize: 24,
      fontWeight: 600,
    },
  },

  // 雷达图样式
  radar: {
    axisLine: {
      lineStyle: {
        color: '#30363d',
      },
    },
    splitLine: {
      lineStyle: {
        color: '#30363d',
      },
    },
    splitArea: {
      areaStyle: {
        color: ['rgba(22, 27, 34, 0.5)', 'rgba(22, 27, 34, 0.2)'],
      },
    },
    axisLabel: {
      color: '#8b949e',
    },
    name: {
      textStyle: {
        color: '#e6edf3',
        fontSize: 12,
      },
    },
  },
}

/**
 * 注册主题到 ECharts
 */
export function registerAdminTheme(echarts) {
  echarts.registerTheme('admin-dark', adminChartTheme)
}

/**
 * 获取图表默认配置
 */
export function getChartDefaultOptions() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: true,
    animationDuration: 500,
    animationEasing: 'cubicOut',
  }
}

/**
 * 状态颜色映射
 */
export const statusColors = {
  normal: '#3fb950',
  warning: '#d29922',
  critical: '#f85149',
  inactive: '#484f58',
  info: '#58a6ff',
}

/**
 * 获取状态颜色
 */
export function getStatusColor(status) {
  return statusColors[status] || statusColors.normal
}

/**
 * 格式化大数字显示
 */
export function formatLargeNumber(num) {
  if (num >= 1e12) return (num / 1e12).toFixed(1) + 'TB'
  if (num >= 1e9) return (num / 1e9).toFixed(1) + 'GB'
  if (num >= 1e6) return (num / 1e6).toFixed(1) + 'MB'
  if (num >= 1e3) return (num / 1e3).toFixed(1) + 'KB'
  return num.toString()
}
