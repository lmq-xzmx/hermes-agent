import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TodoEntry from '../TodoEntry.vue'

describe('TodoEntry.vue', () => {
  describe('Props', () => {
    it('renders title correctly', () => {
      const wrapper = mount(TodoEntry, {
        props: { title: '测试待办' }
      })
      expect(wrapper.find('.todo-entry__title').text()).toBe('测试待办')
    })

    it('renders badge with task count', () => {
      const tasks = [
        { id: '1', type: 'team_join', applicant_name: 'User1' },
        { id: '2', type: 'team_member_exit', applicant_name: 'User2' }
      ]
      const wrapper = mount(TodoEntry, {
        props: { tasks }
      })
      expect(wrapper.find('.todo-entry__badge').text()).toBe('2')
    })

    it('does not show badge when tasks is empty', () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: [] }
      })
      expect(wrapper.find('.todo-entry__badge').exists()).toBe(false)
    })

    it('renders empty state when no tasks', () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: [], emptyText: '没有待办' }
      })
      expect(wrapper.find('.todo-entry__empty').text()).toContain('没有待办')
    })

    it('uses custom empty text', () => {
      const wrapper = mount(TodoEntry, {
        props: { emptyText: '暂无可处理任务' }
      })
      expect(wrapper.find('.todo-entry__empty').text()).toContain('暂无可处理任务')
    })
  })

  describe('Loading state', () => {
    it('shows loading spinner when loading=true', () => {
      const wrapper = mount(TodoEntry, {
        props: { loading: true }
      })
      expect(wrapper.find('.todo-entry__loading').exists()).toBe(true)
      expect(wrapper.find('.todo-entry__spinner').exists()).toBe(true)
    })

    it('hides task list when loading', () => {
      const wrapper = mount(TodoEntry, {
        props: {
          loading: true,
          tasks: [{ id: '1', type: 'team_join', applicant_name: 'User' }]
        }
      })
      expect(wrapper.find('.todo-entry__list').exists()).toBe(false)
    })
  })

  describe('Task item rendering', () => {
    const sampleTasks = [
      {
        id: '1',
        type: 'team_join',
        applicant_name: '张三',
        team_name: 'AI团队',
        reason: '希望参与AI项目开发',
        created_at: new Date().toISOString()
      },
      {
        id: '2',
        type: 'team_member_exit',
        applicant_name: '李四',
        team_name: 'AI团队',
        reason: '工作调动',
        created_at: new Date(Date.now() - 3600000).toISOString()
      }
    ]

    it('renders correct number of tasks', () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: sampleTasks }
      })
      expect(wrapper.findAll('.todo-entry__item')).toHaveLength(2)
    })

    it('displays task type name', () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: sampleTasks }
      })
      const firstItemType = wrapper.findAll('.todo-entry__item-type')[0]
      expect(firstItemType.text()).toBe('申请加入团队')
    })

    it('displays applicant name', () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: sampleTasks }
      })
      const firstItemApplicant = wrapper.findAll('.todo-entry__item-applicant')[0]
      expect(firstItemApplicant.text()).toBe('张三')
    })

    it('displays team name', () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: sampleTasks }
      })
      const firstItemTeam = wrapper.findAll('.todo-entry__item-team')[0]
      expect(firstItemTeam.text()).toBe('AI团队')
    })

    it('displays reason when provided', () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: sampleTasks }
      })
      const firstItemReason = wrapper.findAll('.todo-entry__item-reason')[0]
      expect(firstItemReason.text()).toBe('希望参与AI项目开发')
    })

    it('does not show reason when not provided', () => {
      const tasksWithoutReason = [
        { id: '1', type: 'team_join', applicant_name: '张三', created_at: new Date().toISOString() }
      ]
      const wrapper = mount(TodoEntry, {
        props: { tasks: tasksWithoutReason }
      })
      expect(wrapper.find('.todo-entry__item-reason').exists()).toBe(false)
    })
  })

  describe('Time formatting', () => {
    it('shows "刚刚" for very recent time', () => {
      const now = new Date().toISOString()
      const wrapper = mount(TodoEntry, {
        props: { tasks: [{ id: '1', type: 'team_join', created_at: now }] }
      })
      expect(wrapper.find('.todo-entry__item-time').text()).toBe('刚刚')
    })

    it('shows minutes ago', () => {
      const fiveMinsAgo = new Date(Date.now() - 5 * 60000).toISOString()
      const wrapper = mount(TodoEntry, {
        props: { tasks: [{ id: '1', type: 'team_join', created_at: fiveMinsAgo }] }
      })
      expect(wrapper.find('.todo-entry__item-time').text()).toBe('5 分钟前')
    })

    it('shows hours ago', () => {
      const twoHoursAgo = new Date(Date.now() - 2 * 3600000).toISOString()
      const wrapper = mount(TodoEntry, {
        props: { tasks: [{ id: '1', type: 'team_join', created_at: twoHoursAgo }] }
      })
      expect(wrapper.find('.todo-entry__item-time').text()).toBe('2 小时前')
    })

    it('shows days ago', () => {
      const threeDaysAgo = new Date(Date.now() - 3 * 86400000).toISOString()
      const wrapper = mount(TodoEntry, {
        props: { tasks: [{ id: '1', type: 'team_join', created_at: threeDaysAgo }] }
      })
      expect(wrapper.find('.todo-entry__item-time').text()).toBe('3 天前')
    })

    it('shows date for older items', () => {
      const oldDate = new Date(Date.now() - 10 * 86400000).toISOString()
      const wrapper = mount(TodoEntry, {
        props: { tasks: [{ id: '1', type: 'team_join', created_at: oldDate }] }
      })
      const timeText = wrapper.find('.todo-entry__item-time').text()
      expect(timeText).toMatch(/\d{4}[-/]\d{1,2}[-/]\d{1,2}/)
    })
  })

  describe('Action buttons', () => {
    const sampleTask = {
      id: '1',
      type: 'team_join',
      applicant_name: '张三',
      created_at: new Date().toISOString()
    }

    it('shows actions by default', () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: [sampleTask] }
      })
      expect(wrapper.find('.todo-entry__item-actions').exists()).toBe(true)
    })

    it('hides actions when showActions=false', () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: [sampleTask], showActions: false }
      })
      expect(wrapper.find('.todo-entry__item-actions').exists()).toBe(false)
    })

    it('uses custom action labels', () => {
      const wrapper = mount(TodoEntry, {
        props: {
          tasks: [sampleTask],
          detailLabel: '详情',
          approveLabel: '同意',
          rejectLabel: '否决'
        }
      })
      const buttons = wrapper.findAll('.todo-entry__btn')
      expect(buttons[0].text()).toBe('详情')
      expect(buttons[1].text()).toBe('同意')
      expect(buttons[2].text()).toBe('否决')
    })

    it('emits view event with task', () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: [sampleTask] }
      })
      wrapper.find('.todo-entry__btn--detail').trigger('click')
      expect(wrapper.emitted('view')).toBeTruthy()
      expect(wrapper.emitted('view')[0][0]).toEqual(sampleTask)
    })

    it('emits approve event with task', () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: [sampleTask] }
      })
      wrapper.find('.todo-entry__btn--approve').trigger('click')
      expect(wrapper.emitted('approve')).toBeTruthy()
      expect(wrapper.emitted('approve')[0][0]).toEqual(sampleTask)
    })

    it('emits reject event with task', () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: [sampleTask] }
      })
      wrapper.find('.todo-entry__btn--reject').trigger('click')
      expect(wrapper.emitted('reject')).toBeTruthy()
      expect(wrapper.emitted('reject')[0][0]).toEqual(sampleTask)
    })
  })

  describe('Refresh button', () => {
    it('shows refresh button by default', () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: [] }
      })
      expect(wrapper.find('.todo-entry__refresh').exists()).toBe(true)
    })

    it('hides refresh button when showRefresh=false', () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: [], showRefresh: false }
      })
      expect(wrapper.find('.todo-entry__refresh').exists()).toBe(false)
    })

    it('emits refresh event on click', () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: [] }
      })
      wrapper.find('.todo-entry__refresh').trigger('click')
      expect(wrapper.emitted('refresh')).toBeTruthy()
    })

    it('shows spinning icon when loading', () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: [], loading: true }
      })
      expect(wrapper.find('.todo-entry__refresh-icon--spinning').exists()).toBe(true)
    })
  })

  describe('Load more', () => {
    it('shows load more button when hasMore=true', () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: [{ id: '1', type: 'team_join', created_at: new Date().toISOString() }], hasMore: true }
      })
      expect(wrapper.find('.todo-entry__footer').exists()).toBe(true)
      expect(wrapper.find('.todo-entry__more').exists()).toBe(true)
    })

    it('does not show load more when hasMore=false', () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: [{ id: '1', type: 'team_join', created_at: new Date().toISOString() }], hasMore: false }
      })
      expect(wrapper.find('.todo-entry__footer').exists()).toBe(false)
    })

    it('emits load-more event', () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: [{ id: '1', type: 'team_join', created_at: new Date().toISOString() }], hasMore: true }
      })
      wrapper.find('.todo-entry__more').trigger('click')
      expect(wrapper.emitted('load-more')).toBeTruthy()
    })
  })

  describe('Task type icons', () => {
    it('shows correct icon for team_join', () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: [{ id: '1', type: 'team_join', created_at: new Date().toISOString() }] }
      })
      expect(wrapper.find('.todo-entry__item-icon').text()).toBe('👥')
    })

    it('shows correct icon for team_member_exit', () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: [{ id: '1', type: 'team_member_exit', created_at: new Date().toISOString() }] }
      })
      expect(wrapper.find('.todo-entry__item-icon').text()).toBe('🚪')
    })

    it('shows correct icon for private_space', () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: [{ id: '1', type: 'private_space', created_at: new Date().toISOString() }] }
      })
      expect(wrapper.find('.todo-entry__item-icon').text()).toBe('📁')
    })

    it('shows default icon for unknown type', () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: [{ id: '1', type: 'unknown_type', created_at: new Date().toISOString() }] }
      })
      expect(wrapper.find('.todo-entry__item-icon').text()).toBe('📋')
    })
  })

  describe('Task type names', () => {
    it('shows correct name for team_join', () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: [{ id: '1', type: 'team_join', created_at: new Date().toISOString() }] }
      })
      expect(wrapper.find('.todo-entry__item-type').text()).toBe('申请加入团队')
    })

    it('shows correct name for team_member_exit', () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: [{ id: '1', type: 'team_member_exit', created_at: new Date().toISOString() }] }
      })
      expect(wrapper.find('.todo-entry__item-type').text()).toBe('成员退出申请')
    })

    it('shows correct name for private_space', () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: [{ id: '1', type: 'private_space', created_at: new Date().toISOString() }] }
      })
      expect(wrapper.find('.todo-entry__item-type').text()).toBe('私人空间申请')
    })

    it('shows "未知类型" for unknown type', () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: [{ id: '1', type: 'unknown', created_at: new Date().toISOString() }] }
      })
      expect(wrapper.find('.todo-entry__item-type').text()).toBe('未知类型')
    })
  })

  describe('Hover effect', () => {
    it('applies hover class on mouse enter', async () => {
      const wrapper = mount(TodoEntry, {
        props: { tasks: [{ id: '1', type: 'team_join', created_at: new Date().toISOString() }] }
      })
      const item = wrapper.find('.todo-entry__item')
      await item.trigger('mouseenter')
      await wrapper.vm.$nextTick()
      expect(item.classes()).toContain('todo-entry__item--hover')
    })
  })
})