# 模块一：Admin 控制台可视化增强 - 详细设计

## 1. 技术架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Admin Frontend                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐│
│  │  概览面板   │  │  存储池管理  │  │  用户空间图  │  │  告警   ││
│  │  Overview   │  │  Pools      │  │  Sankey     │  │  Alert  ││
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └────┬────┘│
│         │                │                │                │     │
│         └────────────────┴────────────────┴────────────────┘     │
│                              │                                  │
│                    ┌─────────▼─────────┐                       │
│                    │  AdminDashboard   │                       │
│                    │    Service        │                       │
│                    └─────────┬─────────┘                       │
└──────────────────────────────┼──────────────────────────────────┘
                               │
┌─────────────────────────────▼──────────────────────────────────┐
│                        Admin Backend                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              AdminAnalyticsService                       │   │
│  │  - get_storage_summary()      # 存储池概览              │   │
│  │  - get_user_space_relations()  # 用户-空间关系           │   │
│  │  - get_quota_heatmap()        # 配额热力图               │   │
│  │  - get_operation_trends()     # 操作趋势                │   │
│  │  - get_active_users()         # 活跃用户                 │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 技术选型

| 层级 | 技术 | 选型理由 |
|------|------|---------|
| 图表库 | ECharts 5.x | 丰富的图表类型，良好的性能 |
| UI 框架 | Vue 3 + Composition API | 现有项目技术栈一致 |
| 状态管理 | Pinia | 轻量级，与 Vue 3 集成良好 |
| 数据获取 | REST API + WebSocket | 实时数据推送 |
| 样式 | CSS Variables + SCSS | 主题变量支持 |

---

## 2. 后端 API 设计

### 2.1 API 端点

```
GET  /api/v1/admin/analytics/overview
GET  /api/v1/admin/analytics/storage-pools
GET  /api/v1/admin/analytics/user-spaces
GET  /api/v1/admin/analytics/quota-heatmap
GET  /api/v1/admin/analytics/operation-trends
GET  /api/v1/admin/analytics/active-users
GET  /api/v1/admin/analytics/alerts
WS   /ws/admin/analytics (实时推送)
```

### 2.2 数据模型

#### GET /api/v1/admin/analytics/overview

**响应结构**：
```json
{
  "summary": {
    "total_users": 128,
    "active_users_7d": 89,
    "new_users_7d": 12,
    "total_teams": 24,
    "total_spaces": 156,
    "total_pools": 3,
    "storage": {
      "total_bytes": 21474836480000,
      "used_bytes": 9663676416000,
      "free_bytes": 11811160064000,
      "usage_rate": 0.45
    }
  },
  "alerts": [
    {
      "id": "alert_001",
      "type": "quota_warning",
      "level": "warning",
      "resource": "Space",
      "resource_id": "space_123",
      "resource_name": "Team-A 项目空间",
      "usage_rate": 0.82,
      "message": "空间配额使用率超过80%",
      "created_at": "2026-05-02T10:00:00Z"
    }
  ],
  "recent_activities": [
    {
      "id": "act_001",
      "user_id": "user_456",
      "username": "张三",
      "action": "file_upload",
      "target": "space_123",
      "target_name": "Team-A 项目空间",
      "result": "success",
      "created_at": "2026-05-02T11:30:00Z"
    }
  ]
}
```

#### GET /api/v1/admin/analytics/storage-pools

**响应结构**：
```json
{
  "pools": [
    {
      "id": "pool_001",
      "name": "本地存储池 A",
      "protocol": "local",
      "base_path": "/data/pool-a",
      "total_bytes": 10737418240000,
      "used_bytes": 6442450944000,
      "free_bytes": 4294967296000,
      "usage_rate": 0.60,
      "team_count": 8,
      "status": "normal",
      "created_at": "2026-04-01T00:00:00Z"
    },
    {
      "id": "pool_002",
      "name": "NAS 存储池",
      "protocol": "nfs",
      "base_path": "nfs://192.168.1.100/storage",
      "total_bytes": 10737418240000,
      "used_bytes": 9663676416000,
      "free_bytes": 1073741824000,
      "usage_rate": 0.90,
      "team_count": 12,
      "status": "critical",
      "created_at": "2026-03-15T00:00:00Z"
    }
  ],
  "summary": {
    "total_pools": 3,
    "total_bytes": 32212254720000,
    "used_bytes": 16106127360000,
    "usage_rate": 0.50
  }
}
```

#### GET /api/v1/admin/analytics/user-spaces

**响应结构（桑基图数据）**：
```json
{
  "nodes": [
    { "id": "user_001", "name": "张三", "type": "user", "role": "admin" },
    { "id": "user_002", "name": "李四", "type": "user", "role": "member" },
    { "id": "team_001", "name": "Team-A", "type": "team" },
    { "id": "team_002", "name": "Team-B", "type": "team" },
    { "id": "space_001", "name": "项目文档", "type": "space" },
    { "id": "space_002", "name": "数据存储", "type": "space" }
  ],
  "links": [
    { "source": "user_001", "target": "team_001", "value": 1, "role": "owner" },
    { "source": "user_002", "target": "team_001", "value": 1, "role": "member" },
    { "source": "team_001", "target": "space_001", "value": 50 },
    { "source": "team_001", "target": "space_002", "value": 30 }
  ],
  "stats": {
    "total_users": 128,
    "total_teams": 24,
    "total_spaces": 156,
    "avg_memberships_per_user": 2.3
  }
}
```

#### GET /api/v1/admin/analytics/quota-heatmap

**响应结构**：
```json
{
  "heatmap": [
    {
      "team_id": "team_001",
      "team_name": "Team-A",
      "spaces": [
        { "space_id": "space_001", "space_name": "项目A", "usage_rate": 0.45, "status": "normal" },
        { "space_id": "space_002", "space_name": "项目B", "usage_rate": 0.82, "status": "warning" },
        { "space_id": "space_003", "space_name": "项目C", "usage_rate": 0.95, "status": "critical" }
      ]
    },
    {
      "team_id": "team_002",
      "team_name": "Team-B",
      "spaces": [
        { "space_id": "space_004", "space_name": "项目D", "usage_rate": 0.35, "status": "normal" },
        { "space_id": "space_005", "space_name": "项目E", "usage_rate": 0.68, "status": "normal" }
      ]
    }
  ],
  "legend": {
    "normal": { "min": 0, "max": 0.6, "color": "#3fb950" },
    "warning": { "min": 0.6, "max": 0.8, "color": "#d29922" },
    "critical": { "min": 0.8, "max": 1.0, "color": "#f85149" }
  }
}
```

### 2.3 后端服务实现

```python
# services/admin_analytics_service.py

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

class AdminAnalyticsService:
    """Admin 数据分析服务"""

    def __init__(self, db_factory, team_service, space_service, user_service):
        self._db = db_factory
        self._team_service = team_service
        self._space_service = space_service
        self._user_service = user_service

    def get_storage_summary(self) -> Dict[str, Any]:
        """获取存储池概览数据"""
        pools = self._team_service.list_pools()

        total_bytes = sum(p["total_bytes"] for p in pools)
        free_bytes = sum(p["free_bytes"] for p in pools)
        used_bytes = total_bytes - free_bytes

        return {
            "total_pools": len(pools),
            "total_bytes": total_bytes,
            "used_bytes": used_bytes,
            "free_bytes": free_bytes,
            "usage_rate": used_bytes / total_bytes if total_bytes > 0 else 0,
            "pools": [self._format_pool(p) for p in pools]
        }

    def _format_pool(self, pool: Dict) -> Dict:
        """格式化存储池数据"""
        usage_rate = (pool["total_bytes"] - pool["free_bytes"]) / pool["total_bytes"] if pool["total_bytes"] > 0 else 0
        status = "critical" if usage_rate > 0.9 else "warning" if usage_rate > 0.7 else "normal"

        return {
            "id": pool["id"],
            "name": pool["name"],
            "protocol": pool["protocol"],
            "base_path": pool["base_path"],
            "total_bytes": pool["total_bytes"],
            "used_bytes": pool["total_bytes"] - pool["free_bytes"],
            "free_bytes": pool["free_bytes"],
            "usage_rate": usage_rate,
            "status": status,
            "team_count": self._get_team_count(pool["id"])
        }

    def get_user_space_relationships(self) -> Dict[str, Any]:
        """获取用户-空间关系（桑基图数据）"""
        users = self._user_service.list_users()
        teams = self._team_service.list_teams()
        spaces = self._space_service.list_spaces()

        nodes = []
        links = []

        # 添加用户节点
        for user in users:
            nodes.append({
                "id": f"user_{user['id']}",
                "name": user["username"],
                "type": "user",
                "role": user.get("role_name", "member")
            })

        # 添加团队节点
        for team in teams:
            nodes.append({
                "id": f"team_{team['id']}",
                "name": team["name"],
                "type": "team"
            })

            # 用户 -> 团队 链接
            members = self._team_service.list_members(team["id"])
            for member in members:
                links.append({
                    "source": f"user_{member['user_id']}",
                    "target": f"team_{team['id']}",
                    "value": 1,
                    "role": member["role"]
                })

            # 团队 -> 空间 链接
            team_spaces = [s for s in spaces if s.get("parent_id") == team["id"]]
            for space in team_spaces:
                nodes.append({
                    "id": f"space_{space['id']}",
                    "name": space["name"],
                    "type": "space"
                })
                file_count = self._get_space_file_count(space["id"])
                links.append({
                    "source": f"team_{team['id']}",
                    "target": f"space_{space['id']}",
                    "value": file_count
                })

        return {
            "nodes": nodes,
            "links": links,
            "stats": {
                "total_users": len(users),
                "total_teams": len(teams),
                "total_spaces": len(spaces),
                "avg_memberships": len(links) / len(users) if users else 0
            }
        }

    def get_quota_heatmap(self) -> Dict[str, Any]:
        """获取配额热力图数据"""
        teams = self._team_service.list_teams()
        heatmap = []

        for team in teams:
            team_spaces = self._space_service.list_spaces(user_id=None)
            team_spaces = [s for s in team_spaces if s.get("parent_id") == team["id"]]

            space_usage = []
            for space in team_spaces:
                usage_rate = space["used_bytes"] / space["max_bytes"] if space["max_bytes"] > 0 else 0
                status = "critical" if usage_rate > 0.8 else "warning" if usage_rate > 0.6 else "normal"

                if status != "normal":  # 只包含警告和危险的
                    space_usage.append({
                        "space_id": space["id"],
                        "space_name": space["name"],
                        "usage_rate": usage_rate,
                        "status": status
                    })

            if space_usage:
                heatmap.append({
                    "team_id": team["id"],
                    "team_name": team["name"],
                    "spaces": space_usage
                })

        return {
            "heatmap": heatmap,
            "legend": {
                "normal": {"min": 0, "max": 0.6, "color": "#3fb950"},
                "warning": {"min": 0.6, "max": 0.8, "color": "#d29922"},
                "critical": {"min": 0.8, "max": 1.0, "color": "#f85149"}
            }
        }

    def get_operation_trends(self, days: int = 30) -> Dict[str, Any]:
        """获取操作趋势数据"""
        session = self._db()
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            # 统计每日操作
            operations = session.query(AuditLog).filter(
                AuditLog.created_at >= start_date
            ).all()

            # 按日期和操作类型聚合
            daily_stats = {}
            for op in operations:
                date_key = op.created_at.strftime("%Y-%m-%d")
                action = op.action

                if date_key not in daily_stats:
                    daily_stats[date_key] = {}

                if action not in daily_stats[date_key]:
                    daily_stats[date_key][action] = 0

                daily_stats[date_key][action] += 1

            # 转换为折线图数据
            series = []
            actions = set()
            for date_stats in daily_stats.values():
                actions.update(date_stats.keys())

            for action in sorted(actions):
                series.append({
                    "name": action,
                    "data": [
                        daily_stats.get(date, {}).get(action, 0)
                        for date in self._date_range(start_date, days)
                    ]
                })

            return {
                "dates": self._date_range(start_date, days),
                "series": series
            }
        finally:
            session.close()

    def get_active_users(self, days: int = 7) -> List[Dict]:
        """获取活跃用户统计"""
        session = self._db()
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            active_users = session.query(AuditLog.user_id).filter(
                AuditLog.created_at >= start_date,
                AuditLog.user_id.isnot(None)
            ).distinct().all()

            result = []
            for (user_id,) in active_users:
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    result.append({
                        "user_id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "last_login": user.last_login.isoformat() if user.last_login else None
                    })

            return result
        finally:
            session.close()
```

---

## 3. 前端组件设计

### 3.1 组件目录结构

```
web/src/
├── components/
│   └── admin/
│       ├── AdminOverview.vue      # 概览面板
│       ├── StoragePoolChart.vue   # 存储池环形图
│       ├── UserSpaceSankey.vue    # 用户空间桑基图
│       ├── QuotaHeatmap.vue       # 配额热力图
│       ├── OperationTrends.vue    # 操作趋势折线图
│       └── AlertList.vue          # 告警列表
├── services/
│   └── adminAnalytics.js         # Admin 分析服务
├── stores/
│   └── adminStore.js              # Admin 状态管理
└── views/
    └── AdminDashboard.vue         # Admin 控制台页面
```

### 3.2 核心组件实现

#### StoragePoolChart.vue（存储池环形图）

```vue
<template>
  <div class="storage-pool-chart">
    <div class="chart-header">
      <h3>存储池使用率</h3>
      <span class="total">{{ formatBytes(totalBytes) }} 总计</span>
    </div>
    <div class="pools-container">
      <div v-for="pool in pools" :key="pool.id" class="pool-card">
        <div class="pool-ring">
          <ECharts :option="getRingOption(pool)" :style="{ width: '120px', height: '120px' }" />
        </div>
        <div class="pool-info">
          <h4>{{ pool.name }}</h4>
          <div class="pool-stats">
            <span class="used">{{ formatBytes(pool.usedBytes) }} 已用</span>
            <span class="free">{{ formatBytes(pool.freeBytes) }} 可用</span>
          </div>
          <div class="pool-status" :class="pool.status">
            {{ pool.status === 'critical' ? '⚠ 告警' : pool.status === 'warning' ? '⚡ 注意' : '✓ 正常' }}
          </div>
          <button class="detail-btn" @click="showPoolDetail(pool)">详情</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  pools: {
    type: Array,
    required: true
  }
})

const totalBytes = computed(() =>
  props.pools.reduce((sum, p) => sum + p.totalBytes, 0)
)

function getRingOption(pool) {
  return {
    series: [{
      type: 'pie',
      radius: ['60%', '85%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 4,
        borderColor: '#1a1f26',
        borderWidth: 2
      },
      label: {
        show: false
      },
      data: [
        {
          value: pool.usedBytes,
          name: '已用',
          itemStyle: { color: pool.status === 'critical' ? '#f85149' : pool.status === 'warning' ? '#d29922' : '#58a6ff' }
        },
        {
          value: pool.freeBytes,
          name: '可用',
          itemStyle: { color: '#30363d' }
        }
      ]
    }],
    graphic: [{
      type: 'text',
      left: 'center',
      top: 'center',
      style: {
        text: `${Math.round(pool.usageRate * 100)}%`,
        fill: '#e6edf3',
        fontSize: 18,
        fontWeight: 'bold'
      }
    }]
  }
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function showPoolDetail(pool) {
  // Emit event to show detail modal
}
</script>

<style scoped>
.storage-pool-chart {
  background: var(--bg-secondary);
  border-radius: 8px;
  padding: 16px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.pools-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.pool-card {
  display: flex;
  gap: 16px;
  padding: 12px;
  background: var(--bg-primary);
  border-radius: 8px;
  border: 1px solid var(--border);
}

.pool-ring {
  flex-shrink: 0;
}

.pool-info {
  flex: 1;
  min-width: 0;
}

.pool-info h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: var(--text-primary);
}

.pool-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  display: inline-block;
  margin: 4px 0;
}

.pool-status.normal { background: rgba(63, 185, 80, 0.2); color: #3fb950; }
.pool-status.warning { background: rgba(210, 153, 34, 0.2); color: #d29922; }
.pool-status.critical { background: rgba(248, 81, 73, 0.2); color: #f85149; }
</style>
```

#### UserSpaceSankey.vue（用户空间桑基图）

```vue
<template>
  <div class="user-space-sankey">
    <div class="chart-header">
      <h3>用户-空间关系</h3>
      <div class="filter">
        <select v-model="filterType" @change="filterNodes">
          <option value="all">全部</option>
          <option value="user">仅用户</option>
          <option value="team">仅团队</option>
          <option value="space">仅空间</option>
        </select>
      </div>
    </div>
    <ECharts :option="sankeyOption" :style="{ width: '100%', height: '400px' }" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Object,
    required: true
  }
})

const filterType = ref('all')

const sankeyOption = computed(() => {
  const nodes = filterType.value === 'all'
    ? props.data.nodes
    : props.data.nodes.filter(n => n.type === filterType.value)

  return {
    tooltip: {
      trigger: 'item',
      triggerOn: 'mousemove'
    },
    series: [{
      type: 'sankey',
      layout: 'none',
      emphasis: { focus: 'adjacency' },
      nodeAlign: 'left',
      nodeGap: 12,
      nodeWidth: 20,
      lineStyle: {
        color: 'gradient',
        curveness: 0.5
      },
      data: nodes.map(n => ({
        name: n.name,
        itemStyle: {
          color: n.type === 'user' ? '#58a6ff' : n.type === 'team' ? '#3fb950' : '#d29922'
        }
      })),
      links: props.data.links.filter(l => {
        const sourceExists = nodes.some(n => n.id === l.source)
        const targetExists = nodes.some(n => n.id === l.target)
        return sourceExists && targetExists
      })
    }]
  }
})

function filterNodes() {
  // Trigger re-render with filtered data
}
</script>
```

#### QuotaHeatmap.vue（配额热力图）

```vue
<template>
  <div class="quota-heatmap">
    <div class="chart-header">
      <h3>配额告警</h3>
      <div class="legend">
        <span class="legend-item normal"><span class="dot"></span> &lt; 60%</span>
        <span class="legend-item warning"><span class="dot"></span> 60-80%</span>
        <span class="legend-item critical"><span class="dot"></span> &gt; 80%</span>
      </div>
    </div>
    <div class="heatmap-container">
      <table class="heatmap-table">
        <thead>
          <tr>
            <th>团队/空间</th>
            <th v-for="space in visibleSpaces" :key="space.space_id">
              {{ space.space_name }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="team in heatmapData" :key="team.team_id">
            <td class="team-name">{{ team.team_name }}</td>
            <td v-for="space in team.spaces" :key="space.space_id"
                :class="['usage-cell', space.status]"
                :title="`${Math.round(space.usage_rate * 100)}%`">
              <div class="usage-bar" :style="{ width: `${space.usage_rate * 100}%` }">
                <span class="usage-text">{{ Math.round(space.usage_rate * 100) }}%</span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  data: {
    type: Object,
    required: true
  }
})

const heatmapData = computed(() => props.data.heatmap || [])

const visibleSpaces = computed(() => {
  const allSpaces = heatmapData.value.flatMap(t => t.spaces)
  return [...new Map(allSpaces.map(s => [s.space_id, s])).values()]
})
</script>

<style scoped>
.quota-heatmap {
  background: var(--bg-secondary);
  border-radius: 8px;
  padding: 16px;
}

.legend {
  display: flex;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.legend-item .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-item.normal .dot { background: #3fb950; }
.legend-item.warning .dot { background: #d29922; }
.legend-item.critical .dot { background: #f85149; }

.heatmap-table {
  width: 100%;
  border-collapse: collapse;
}

.heatmap-table th,
.heatmap-table td {
  padding: 8px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}

.team-name {
  font-weight: 500;
  color: var(--text-primary);
}

.usage-cell {
  position: relative;
  padding: 4px 8px !important;
}

.usage-bar {
  height: 20px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 4px;
  min-width: 40px;
}

.usage-cell.normal .usage-bar { background: rgba(63, 185, 80, 0.3); }
.usage-cell.warning .usage-bar { background: rgba(210, 153, 34, 0.3); }
.usage-cell.critical .usage-bar { background: rgba(248, 81, 73, 0.3); }

.usage-text {
  font-size: 11px;
  color: var(--text-secondary);
}
</style>
```

### 3.3 状态管理 (adminStore.js)

```javascript
// stores/adminStore.js
import { defineStore } from 'pinia'
import { adminAnalyticsApi } from '@/services/adminAnalytics'

export const useAdminStore = defineStore('admin', {
  state: () => ({
    overview: null,
    storagePools: [],
    userSpaces: { nodes: [], links: [] },
    quotaHeatmap: { heatmap: [], legend: {} },
    operationTrends: { dates: [], series: [] },
    activeUsers: [],
    alerts: [],
    loading: false,
    error: null,
    lastUpdated: null
  }),

  getters: {
    totalStorage: (state) => {
      if (!state.storagePools.length) return 0
      return state.storagePools.reduce((sum, p) => sum + p.totalBytes, 0)
    },
    usedStorage: (state) => {
      if (!state.storagePools.length) return 0
      return state.storagePools.reduce((sum, p) => sum + p.usedBytes, 0)
    },
    criticalAlerts: (state) => state.alerts.filter(a => a.level === 'critical'),
    warningAlerts: (state) => state.alerts.filter(a => a.level === 'warning')
  },

  actions: {
    async fetchOverview() {
      this.loading = true
      try {
        const data = await adminAnalyticsApi.getOverview()
        this.overview = data.summary
        this.alerts = data.alerts || []
        this.lastUpdated = new Date()
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },

    async fetchStoragePools() {
      try {
        const data = await adminAnalyticsApi.getStoragePools()
        this.storagePools = data.pools
      } catch (e) {
        this.error = e.message
      }
    },

    async fetchUserSpaces() {
      try {
        const data = await adminAnalyticsApi.getUserSpaces()
        this.userSpaces = data
      } catch (e) {
        this.error = e.message
      }
    },

    async fetchQuotaHeatmap() {
      try {
        const data = await adminAnalyticsApi.getQuotaHeatmap()
        this.quotaHeatmap = data
      } catch (e) {
        this.error = e.message
      }
    },

    async fetchAll() {
      await Promise.all([
        this.fetchOverview(),
        this.fetchStoragePools(),
        this.fetchUserSpaces(),
        this.fetchQuotaHeatmap()
      ])
    },

    setupWebSocket() {
      const ws = new WebSocket('ws://localhost:8080/ws/admin/analytics')

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        switch (data.type) {
          case 'quota_update':
            this.updateQuota(data.payload)
            break
          case 'alert':
            this.alerts.push(data.payload)
            break
        }
      }

      ws.onclose = () => {
        // Reconnect after 5 seconds
        setTimeout(() => this.setupWebSocket(), 5000)
      }
    }
  }
})
```

### 3.4 Admin 控制台页面 (AdminDashboard.vue)

```vue
<template>
  <div class="admin-dashboard">
    <header class="dashboard-header">
      <h1>管理控制台</h1>
      <div class="header-actions">
        <button @click="refresh" class="btn btn-secondary">
          🔄 刷新
        </button>
        <select v-model="refreshInterval" @change="setupAutoRefresh">
          <option :value="0">手动刷新</option>
          <option :value="30000">30秒</option>
          <option :value="60000">1分钟</option>
          <option :value="300000">5分钟</option>
        </select>
      </div>
    </header>

    <div v-if="loading" class="loading">
      加载中...
    </div>

    <div v-else class="dashboard-grid">
      <!-- 概览卡片 -->
      <div class="overview-cards">
        <div class="stat-card">
          <span class="stat-icon">👥</span>
          <div class="stat-content">
            <span class="stat-value">{{ overview?.total_users || 0 }}</span>
            <span class="stat-label">总用户</span>
          </div>
        </div>
        <div class="stat-card">
          <span class="stat-icon">📁</span>
          <div class="stat-content">
            <span class="stat-value">{{ overview?.total_spaces || 0 }}</span>
            <span class="stat-label">总空间</span>
          </div>
        </div>
        <div class="stat-card">
          <span class="stat-icon">💾</span>
          <div class="stat-content">
            <span class="stat-value">{{ formatBytes(overview?.storage?.used_bytes) }}</span>
            <span class="stat-label">已用存储</span>
          </div>
        </div>
        <div class="stat-card" :class="{ 'alert': criticalAlerts.length > 0 }">
          <span class="stat-icon">⚠️</span>
          <div class="stat-content">
            <span class="stat-value">{{ alerts.length }}</span>
            <span class="stat-label">活跃告警</span>
          </div>
        </div>
      </div>

      <!-- 存储池图表 -->
      <StoragePoolChart :pools="storagePools" class="chart-section" />

      <!-- 用户空间关系图 -->
      <UserSpaceSankey :data="userSpaces" class="chart-section" />

      <!-- 配额热力图 -->
      <QuotaHeatmap :data="quotaHeatmap" class="chart-section" />

      <!-- 操作趋势 -->
      <OperationTrends :data="operationTrends" class="chart-section" />

      <!-- 告警列表 -->
      <AlertList :alerts="alerts" class="chart-section" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useAdminStore } from '@/stores/adminStore'
import StoragePoolChart from '@/components/admin/StoragePoolChart.vue'
import UserSpaceSankey from '@/components/admin/UserSpaceSankey.vue'
import QuotaHeatmap from '@/components/admin/QuotaHeatmap.vue'
import OperationTrends from '@/components/admin/OperationTrends.vue'
import AlertList from '@/components/admin/AlertList.vue'

const store = useAdminStore()
const { overview, storagePools, userSpaces, quotaHeatmap, operationTrends, alerts, loading } = storeToRefs(store)

const refreshInterval = ref(60000)
let refreshTimer = null

onMounted(async () => {
  await store.fetchAll()
  store.setupWebSocket()
  setupAutoRefresh()
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})

function setupAutoRefresh() {
  if (refreshTimer) clearInterval(refreshTimer)
  if (refreshInterval.value > 0) {
    refreshTimer = setInterval(() => store.fetchAll(), refreshInterval.value)
  }
}

async function refresh() {
  await store.fetchAll()
}

function formatBytes(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}
</script>

<style scoped>
.admin-dashboard {
  padding: 20px;
  background: var(--bg-primary);
  min-height: 100vh;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 16px;
}

.overview-cards {
  grid-column: span 12;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.chart-section {
  grid-column: span 6;
}

.stat-card {
  background: var(--bg-secondary);
  border-radius: 8px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-card.alert {
  border: 1px solid #f85149;
  background: rgba(248, 81, 73, 0.1);
}

.stat-icon {
  font-size: 24px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  display: block;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.loading {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}
</style>
```

---

## 4. 测试策略

### 4.1 单元测试

```python
# tests/test_admin_analytics_service.py
import pytest
from datetime import datetime, timedelta

class TestAdminAnalyticsService:
    """Admin 分析服务单元测试"""

    def test_get_storage_summary(self, service):
        result = service.get_storage_summary()

        assert "total_pools" in result
        assert "total_bytes" in result
        assert "usage_rate" in result
        assert result["total_pools"] >= 0

    def test_get_storage_summary_empty(self, empty_db):
        service = AdminAnalyticsService(empty_db, team_service, space_service, user_service)
        result = service.get_storage_summary()

        assert result["total_pools"] == 0
        assert result["usage_rate"] == 0

    def test_get_user_space_relationships(self, service, sample_data):
        result = service.get_user_space_relationships()

        assert "nodes" in result
        assert "links" in result
        assert "stats" in result
        assert len(result["nodes"]) > 0
        assert len(result["links"]) > 0

    def test_quota_heatmap_filters_warning(self, service):
        result = service.get_quota_heatmap()

        # 只包含警告和危险的条目
        for team in result["heatmap"]:
            for space in team["spaces"]:
                assert space["status"] in ["warning", "critical"]

    def test_operation_trends_date_range(self, service):
        result = service.get_operation_trends(days=30)

        assert "dates" in result
        assert "series" in result
        assert len(result["dates"]) == 30
```

### 4.2 集成测试

```javascript
// e2e/admin-dashboard.spec.js
describe('Admin Dashboard', () => {
  beforeEach(async () => {
    await loginAsAdmin()
    await page.goto('/admin/dashboard')
  })

  it('displays storage pool chart', async () => {
    await waitForSelector('.storage-pool-chart')
    const poolCards = await page.locator('.pool-card').count()
    expect(poolCards).toBeGreaterThan(0)
  })

  it('updates data in real-time', async () => {
    // Upload file to trigger storage update
    await uploadFileToTeam()

    // Wait for WebSocket update
    await waitForTimeout(2000)

    // Verify chart updated
    const usedBytes = await page.locator('.pool-card:first-child .used').textContent()
    expect(usedBytes).not.toBe('0 B')
  })

  it('navigates to pool detail', async () => {
    await page.click('.pool-card:first-child .detail-btn')
    await expect(page.url()).toContain('/admin/pools/')
  })
})
```

---

## 5. 性能优化

### 5.1 数据缓存策略

```javascript
// services/adminAnalytics.js
const CACHE_TTL = 5 * 60 * 1000 // 5 minutes

const cache = new Map()

export const adminAnalyticsApi = {
  async getStoragePools() {
    const cached = cache.get('storage_pools')
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
      return cached.data
    }

    const data = await fetch('/api/v1/admin/analytics/storage-pools')
    cache.set('storage_pools', { data, timestamp: Date.now() })
    return data
  }
}
```

### 5.2 虚拟化长列表

```javascript
// 对于超过 100 个节点，使用虚拟化渲染
import { useVirtualList } from '@vueuse/core'

const visibleNodes = useVirtualList(allNodes, {
  itemHeight: 40,
  overscan: 10
})
```

---

## 6. 部署配置

### 6.1 环境变量

```bash
# .env.admin
ADMIN_CACHE_TTL=300000
ADMIN_REALTIME_ENABLED=true
ADMIN_WS_ENDPOINT=ws://localhost:8080/ws/admin/analytics
```

### 6.2 Nginx 配置

```nginx
location /admin {
    proxy_pass http://localhost:8080;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```