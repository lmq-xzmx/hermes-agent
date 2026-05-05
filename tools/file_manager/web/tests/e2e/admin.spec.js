// web/tests/e2e/admin.spec.js
// T10: Admin功能E2E测试
//
// 注意: Admin dashboard 是独立的 Vue 应用 (src/views/admin/)，未集成到主 app.html
// 这些测试验证 Admin 功能不在 Web-First 主应用中
// Admin 功能由独立的 Vue 应用提供，测试在 Vue 应用中进行

import { test, expect } from '@playwright/test'

test.describe('Admin功能E2E测试', () => {
  test('主应用中不包含 Admin dashboard 视图', async ({ page }) => {
    // 加载主页面 - Vue SPA
    await page.goto('http://localhost:5173/vue.html', { waitUntil: 'networkidle' });

    // 等待 Vue 应用挂载
    await page.waitForTimeout(2000);

    // 验证 #view-admin 不存在于主应用中
    const adminView = page.locator('#view-admin')
    await expect(adminView).toHaveCount(0)
  })

  test('Vue SPA 应用正常加载', async ({ page }) => {
    await page.goto('http://localhost:5173/vue.html', { waitUntil: 'networkidle' });

    // 等待 Vue 应用挂载
    await page.waitForTimeout(2000);

    // 验证 #app 元素存在
    const app = page.locator('#app')
    await expect(app).toBeAttached()

    // 验证页面有内容渲染（不是空白页）
    const bodyContent = await page.locator('body').innerHTML()
    expect(bodyContent.length).toBeGreaterThan(50)
  })
})
