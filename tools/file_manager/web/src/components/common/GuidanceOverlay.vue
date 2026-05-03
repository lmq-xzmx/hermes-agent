<template>
  <GuidanceModal
    v-model="guidanceStore.modalVisible"
    :title="guidanceStore.modalConfig.title"
    :message="guidanceStore.modalConfig.message"
    :icon="guidanceStore.modalConfig.icon"
    :actions="guidanceStore.modalConfig.actions"
    :on-dismiss-type="handleDismiss"
    :dismiss-event-name="guidanceStore.currentEventName"
    @action="handleAction"
  />
</template>

<script setup>
import { useGuidanceStore } from '@/stores/guidanceStore'
import GuidanceModal from '@/components/common/GuidanceModal.vue'

const guidanceStore = useGuidanceStore()

function handleAction(action) {
  guidanceStore.executeAction(action)
}

function handleDismiss(eventName) {
  if (eventName) {
    guidanceStore.dismiss(eventName)
  }
}
</script>
