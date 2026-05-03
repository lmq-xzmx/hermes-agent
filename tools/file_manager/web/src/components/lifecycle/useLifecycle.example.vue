<!--
  Vue 3 组件中使用 Lifecycle 拦截器的示例

  用法:
  1. 在组件中引入 useLifecycle
  2. 调用 beforeAction() 检查约束
  3. 如果 allowed=false，显示弹窗
-->
<template>
  <div>
    <button @click="handleUpload">上传文件</button>
    <button @click="handleDeleteTeam">删除团队</button>

    <GuidanceModal
      v-model="showGuidance"
      :title="guidanceConfig.title"
      :message="guidanceConfig.message"
      :icon="guidanceConfig.icon"
      :guidance="guidanceConfig.guidance"
      @action="handleGuidanceAction"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useLifecycle } from '@/composables/useLifecycle'
import GuidanceModal from '@/components/common/GuidanceModal.vue'

const {
  beforeAction,
  showGuidanceModal,
  registerGuidanceCallback
} = useLifecycle()

const showGuidance = ref(false)
const guidanceConfig = ref({})

// 注册回调
registerGuidanceCallback('showContactAdminModal', () => {
  console.log('显示联系管理员弹窗')
})

async function handleUpload() {
  const context = {
    isMember: true, // 从 store 或 props 获取
    hasQuota: true  // 从 API 获取
  }

  const result = await beforeAction('upload_file', context)

  if (!result.allowed) {
    guidanceConfig.value = result
    showGuidance.value = true
    return
  }

  // 继续上传逻辑...
  console.log('执行上传')
}

async function handleDeleteTeam() {
  const context = {
    isOwner: true  // 检查当前用户是否是团队所有者
  }

  const result = await beforeAction('delete_team', context)

  if (!result.allowed) {
    guidanceConfig.value = result
    showGuidance.value = true
    return
  }

  // 继续删除逻辑...
  console.log('执行删除团队')
}

function handleGuidanceAction(guidance) {
  if (guidance.path) {
    window.location.hash = guidance.path
  } else if (guidance.action) {
    // 执行对应回调
    console.log('执行引导操作:', guidance.action)
  }
}
</script>
