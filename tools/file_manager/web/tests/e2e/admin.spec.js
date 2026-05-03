// web/tests/e2e/admin.spec.js
// T10: Admin功能E2E测试

import { test, expect } from '@playwright/test'

test.describe('Admin功能E2E测试', () => {
  test.beforeEach(async ({ page }) => {
    // 加载主页面 (file:// for local dev)
    await page.goto('file:///Users/xzmx/Downloads/my-project/hermes-agent/tools/file_manager/web/app.html')
    await page.waitForLoadState('domcontentloaded')

    // 检查是否需要登录
    const loginScreen = page.locator('#loginScreen')
    if (await loginScreen.isVisible()) {
      // 先注册一个测试用户
      await page.click('#showRegister')
      await page.waitForTimeout(300)
      const timestamp = Date.now()
      await page.fill('#regUsername', `admin_test_${timestamp}`)
      await page.fill('#regPassword', 'Test123456')
      await page.fill('#regPassword2', 'Test123456')
      await page.click('#registerForm button[type="submit"]')
      // 等待注册完成或跳转到主界面
      await page.waitForTimeout(1000)
    }

    // 使用SPA内部导航到Admin视图
    await page.evaluate(() => navigateTo('admin'))
    await page.waitForTimeout(500) // 等待视图切换和数据加载
  })

  test('AdminOverview 统计数据卡片显示', async ({ page }) => {
    // 验证6个统计卡片正确显示
    await expect(page.locator('.stat-card')).toHaveCount(6)

    // 验证卡片内容 - 总用户
    const totalUsersCard = page.locator('.stat-card').filter({ hasText: '总用户' })
    await expect(totalUsersCard).toBeVisible()
    await expect(totalUsersCard.locator('.stat-value')).not.toHaveText('')

    // 验证卡片内容 - 总空间
    const totalSpacesCard = page.locator('.stat-card').filter({ hasText: '总空间' })
    await expect(totalSpacesCard).toBeVisible()

    // 验证卡片内容 - 已用存储
    const storageCard = page.locator('.stat-card').filter({ hasText: '已用存储' })
    await expect(storageCard).toBeVisible()
    await expect(storageCard.locator('.storage-bar')).toBeVisible()
  })

  test('AdminOverview 数字格式化正确', async ({ page }) => {
    // 存储使用量应该是格式化后的数字+单位
    const storageValue = page.locator('.stat-card').filter({ hasText: '已用存储' }).locator('.stat-value')
    const text = await storageValue.textContent()
    // 验证格式: 数字 + 空格 + 单位(B/KB/MB/GB/TB)
    expect(text).toMatch(/^\d+(\.\d+)?\s+[BKMGT]B?$|^-?$/)
  })

  test('AdminOverview 点击跳转功能', async ({ page }) => {
    // 点击"总用户"卡片
    const totalUsersCard = page.locator('.stat-card').filter({ hasText: '总用户' })
    await totalUsersCard.click()
    // 验证视图保持
    await expect(page.locator('.view-container.active')).toBeVisible()
  })

  test('AdminOverview 存储使用率进度条', async ({ page }) => {
    const storageCard = page.locator('.stat-card').filter({ hasText: '已用存储' })
    const storageBar = storageCard.locator('.storage-bar-fill')
    await expect(storageBar).toBeVisible()
  })

  test('AdminOverview Loading状态', async ({ page }) => {
    // 刷新页面后导航到admin
    await page.reload()
    await page.evaluate(() => navigateTo('admin'))
    await page.waitForTimeout(500)
    // 验证admin视图显示
    await expect(page.locator('#view-admin')).toHaveClass(/active/)
  })
})
