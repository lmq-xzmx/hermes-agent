<template>
  <nav class="breadcrumb" aria-label="面包屑导航">
    <ol class="breadcrumb-list">
      <li
        v-for="(crumb, index) in crumbs"
        :key="index"
        class="breadcrumb-item"
      >
        <span v-if="index > 0" class="breadcrumb-separator" aria-hidden="true">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M4.5 9L7.5 6L4.5 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </span>
        <component
          :is="crumb.to ? 'a' : 'span'"
          class="breadcrumb-link"
          :class="{ clickable: !!crumb.to || crumb.clickable }"
          :href="crumb.to"
          @click="crumb.clickable && crumb.onClick && crumb.onClick()"
        >
          <span v-if="crumb.icon" class="breadcrumb-icon">{{ crumb.icon }}</span>
          {{ crumb.label }}
        </component>
      </li>
    </ol>
  </nav>
</template>

<script setup>
defineProps({
  crumbs: {
    type: Array,
    required: true
    // { label: string, to?: string, icon?: string, clickable?: boolean, onClick?: function }
  }
})
</script>

<style scoped>
.breadcrumb {
  padding: var(--spacing-sm) 0;
}

.breadcrumb-list {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  list-style: none;
  margin: 0;
  padding: 0;
}

.breadcrumb-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.breadcrumb-separator {
  color: var(--color-ink-muted-48);
  display: flex;
  align-items: center;
}

.breadcrumb-link {
  font-family: var(--font-family-text);
  font-size: 14px;
  line-height: 1.43;
  letter-spacing: -0.224px;
  color: var(--color-ink-muted-48);
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: var(--radius-md);
  transition: all 0.15s ease;
}

.breadcrumb-link.clickable {
  color: var(--color-ink);
}

.breadcrumb-link.clickable:hover {
  background: var(--color-surface-pearl);
  color: var(--color-primary);
}

.breadcrumb-link:active {
  transform: scale(0.98);
}

.breadcrumb-icon {
  font-size: 14px;
}
</style>
