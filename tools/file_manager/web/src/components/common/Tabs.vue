<template>
  <div class="tabs">
    <div class="tabs-list" role="tablist">
      <button
        v-for="(tab, index) in tabs"
        :key="tab.value || index"
        class="tab-item"
        :class="{ active: modelValue === (tab.value || index) }"
        :aria-selected="modelValue === (tab.value || index)"
        role="tab"
        @click="selectTab(tab.value || index)"
      >
        <span v-if="tab.icon" class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-label">{{ tab.label }}</span>
        <span v-if="tab.badge" class="tab-badge">{{ tab.badge }}</span>
      </button>
    </div>
    <div class="tabs-content" role="tabpanel">
      <slot :name="modelValue" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  modelValue: { type: [String, Number], required: true },
  tabs: {
    type: Array,
    required: true
    // { label: string, value?: string|number, icon?: string, badge?: string|number }
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

function selectTab(value) {
  emit('update:modelValue', value)
  emit('change', value)
}
</script>

<style scoped>
.tabs {
  width: 100%;
}

.tabs-list {
  display: flex;
  gap: var(--spacing-xxs);
  border-bottom: 1px solid var(--color-hairline);
  padding-bottom: 0;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-lg);
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  font-family: var(--font-family-text);
  font-size: 15px;
  color: var(--color-ink-muted-48);
  cursor: pointer;
  transition: all 0.15s ease;
  margin-bottom: -1px;
}

.tab-item:hover {
  color: var(--color-ink);
  background: var(--color-surface-pearl);
}

.tab-item.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}

.tab-item:active {
  transform: scale(0.98);
}

.tab-icon {
  font-size: 16px;
}

.tab-badge {
  font-size: 11px;
  padding: 2px 6px;
  background: var(--color-surface-pearl);
  border-radius: var(--radius-pill);
  color: var(--color-ink-muted-48);
}

.tab-item.active .tab-badge {
  background: var(--color-primary-hover);
  color: var(--color-primary);
}

.tabs-content {
  padding-top: var(--spacing-md);
}
</style>
