<template>
  <GuidanceModal
    v-model="lifecycleStore.modalVisible"
    :title="lifecycleStore.modalConfig.title"
    :message="lifecycleStore.modalConfig.message"
    :icon="lifecycleStore.modalConfig.icon"
    :guidance="lifecycleStore.modalConfig.guidance"
    :on-dismiss-type="handleDismissForever"
    @action="handleAction"
    @dismiss="handleDismiss"
  />
  <slot />
</template>

<script setup>
import { onMounted } from 'vue'
import { useLifecycleStore } from '@/stores/lifecycleStore'
import GuidanceModal from '@/components/common/GuidanceModal.vue'

const lifecycleStore = useLifecycleStore()

function handleAction(guidance) {
  lifecycleStore.executeGuidance(guidance)
}

function handleDismiss() {
  lifecycleStore.closeModal()
}

// 处理"不再显示" - 生命周期约束基于上下文，关闭即可（不永久忽略）
function handleDismissForever() {
  lifecycleStore.dismissGuidance()
}

onMounted(() => {
  // 注册默认回调
  lifecycleStore.registerGuidanceCallback('showContactAdminModal', () => {
    // 触发管理员联系弹窗
    console.log('联系管理员')
  })
})
</script>
