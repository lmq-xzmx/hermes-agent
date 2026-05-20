<template>
  <div class="tabs">
    <div class="tabs__list" role="tablist">
      <button
        v-for="(tab, index) in tabs"
        :key="tab.value || index"
        class="tabs__item"
        :class="{ 'tabs__item--active': modelValue === (tab.value || index) }"
        :aria-selected="modelValue === (tab.value || index)"
        role="tab"
        @click="selectTab(tab.value || index)"
      >
        <span v-if="tab.icon" class="tabs__icon">{{ tab.icon }}</span>
        <span class="tabs__label">{{ tab.label }}</span>
        <span v-if="tab.badge" class="tabs__badge">{{ tab.badge }}</span>
      </button>
    </div>
    <div class="tabs__content" role="tabpanel">
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
/* ============================================
   Tabs - Apple Design System
   ============================================ */

.tabs {
  /* Layout */
  display: flex;
  flex-direction: column;
}

/* ============================================
   Element: tabs__list
   ============================================ */
.tabs__list {
  /* Layout */
  display: flex;
  gap: var(--spacing-xs);
  padding-bottom: var(--spacing-sm);
  margin-bottom: var(--spacing-md);

  /* Visual */
  border-bottom: 1px solid var(--color-hairline);
}

/* ============================================
   Element: tabs__item
   ============================================ */
.tabs__item {
  /* Layout */
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xxs);

  /* Box Model */
  padding: var(--spacing-xxs) var(--spacing-lg);

  /* Visual */
  background: transparent;
  color: var(--color-ink-muted-48);
  border: none;
  border-radius: var(--radius-pill);

  /* Typography */
  font: var(--text-body);
  cursor: pointer;

  /* Animation */
  transition: background 0.15s ease, color 0.15s ease;
}

.tabs__item:hover {
  background: var(--color-canvas-parchment);
  color: var(--color-ink);
}

.tabs__item:active {
  transform: scale(0.95);
}

/* Active State */
.tabs__item--active {
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.tabs__item--active:hover {
  background: var(--color-primary);
  color: var(--color-on-primary);
}

/* ============================================
   Element: tabs__icon
   ============================================ */
.tabs__icon {
  font-size: 16px;
}

/* ============================================
   Element: tabs__label
   ============================================ */
.tabs__label {
  /* Typography */
  font: inherit;
}

/* ============================================
   Element: tabs__badge
   ============================================ */
.tabs__badge {
  /* Typography */
  font: var(--text-caption);
}

/* ============================================
   Element: tabs__content
   ============================================ */
.tabs__content {
  /* Layout */
  flex: 1;
}
</style>