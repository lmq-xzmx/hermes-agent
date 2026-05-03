/**
 * Lifecycle 模块导出
 *
 * 使用方式:
 *
 * // 方式1: Composable (推荐)
 * import { useLifecycle } from '@/components/lifecycle'
 *
 * // 方式2: Pinia Store
 * import { useLifecycleStore } from '@/stores/lifecycleStore'
 *
 * // 方式3: Vue Component (统一弹窗)
 * import GuidanceModal from '@/components/common/GuidanceModal.vue'
 * import LifecycleProvider from '@/components/lifecycle/LifecycleProvider.vue'
 */
export { useLifecycle } from '@/composables/useLifecycle'
export { useLifecycleStore } from '@/stores/lifecycleStore'
export { default as GuidanceModal } from '@/components/common/GuidanceModal.vue'
export { default as LifecycleProvider } from '@/components/lifecycle/LifecycleProvider.vue'
