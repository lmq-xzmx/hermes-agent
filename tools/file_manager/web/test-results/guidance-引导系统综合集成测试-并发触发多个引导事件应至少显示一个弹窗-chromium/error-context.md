# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: guidance.spec.js >> 引导系统综合集成测试 >> 并发触发多个引导事件应至少显示一个弹窗
- Location: tests/e2e/guidance.spec.js:355:3

# Error details

```
Error: expect(received).toBeGreaterThan(expected)

Expected: > 0
Received:   0
```

# Page snapshot

```yaml
- generic [ref=e6]:
  - heading "Hermes 文件管理器 v1.0" [level=1] [ref=e7]
  - paragraph [ref=e8]: 登录以访问您的文件
  - generic [ref=e9]:
    - generic [ref=e10]:
      - generic [ref=e11]: 用户名
      - textbox "用户名" [ref=e12]
    - generic [ref=e13]:
      - generic [ref=e14]: 密码
      - generic [ref=e15]:
        - textbox "密码" [ref=e16]
        - button "👁" [ref=e17] [cursor=pointer]
    - generic [ref=e18]:
      - checkbox "记住账号密码" [ref=e19]
      - generic [ref=e20]: 记住账号密码
    - button "登录" [ref=e21] [cursor=pointer]
  - paragraph [ref=e22]:
    - text: 没有账户？
    - link "立即注册" [ref=e23] [cursor=pointer]:
      - /url: "#"
```

# Test source

```ts
  269 |       // 重置 Vue store 内存状态
  270 |       if (window.__vueGuidance && window.__vueGuidance.resetGuidance) {
  271 |         window.__vueGuidance.resetGuidance();
  272 |       }
  273 |     });
  274 |   });
  275 | 
  276 |   /**
  277 |    * 测试: 完整引导流程
  278 |    * 各阶段正确触发对应引导
  279 |    */
  280 |   test('完整引导流程: 各阶段正确触发对应引导', async ({ page }) => {
  281 |     // Step 1: 触发 USER_REGISTERED
  282 |     await page.evaluate(() => {
  283 |       if (window.triggerGuidance) {
  284 |         window.triggerGuidance('USER_REGISTERED', { teams: [], isFirstUser: true });
  285 |       }
  286 |     });
  287 |     await page.waitForTimeout(500);
  288 | 
  289 |     let modalVisible = await page.locator('.guidance-modal-overlay').isVisible().catch(() => false);
  290 |     expect(modalVisible).toBeTruthy();
  291 | 
  292 |     // 关闭弹窗
  293 |     const closeBtn = page.locator('.guidance-close');
  294 |     if (await closeBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
  295 |       await closeBtn.first().click();
  296 |     }
  297 |     await page.waitForTimeout(300);
  298 | 
  299 |     // Step 2: 触发 TEAM_JOINED
  300 |     await page.evaluate(() => {
  301 |       if (window.triggerGuidance) {
  302 |         window.triggerGuidance('TEAM_JOINED', { isFirstJoin: true, teamId: 'team-1' });
  303 |       }
  304 |     });
  305 |     await page.waitForTimeout(500);
  306 | 
  307 |     modalVisible = await page.locator('.guidance-modal-overlay').isVisible().catch(() => false);
  308 |     expect(modalVisible).toBeTruthy();
  309 |   });
  310 | 
  311 |   /**
  312 |    * 测试: 引导系统状态一致性
  313 |    */
  314 |   test('引导系统状态应在刷新后保持一致', async ({ page }) => {
  315 |     // 确保 Vue 应用已加载
  316 |     await page.waitForFunction(() => typeof window.__vueGuidance !== 'undefined', { timeout: 5000 });
  317 | 
  318 |     // 触发引导
  319 |     await page.evaluate(() => {
  320 |       if (window.triggerGuidance) {
  321 |         window.triggerGuidance('USER_REGISTERED', { teams: [], isFirstUser: true });
  322 |       }
  323 |     });
  324 | 
  325 |     await page.waitForTimeout(500);
  326 | 
  327 |     // 关闭弹窗
  328 |     const closeBtn = page.locator('.guidance-close');
  329 |     if (await closeBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
  330 |       await closeBtn.first().click();
  331 |     }
  332 |     await page.waitForTimeout(300);
  333 | 
  334 |     // 刷新页面
  335 |     await page.reload();
  336 |     await page.waitForTimeout(500);
  337 | 
  338 |     // 验证引导不重复显示 (因为已忽略)
  339 |     const modalVisible = await page.locator('.guidance-modal-overlay').isVisible().catch(() => false);
  340 |     expect(modalVisible).toBeFalsy();
  341 | 
  342 |     // 验证 localStorage 状态 - Vue 使用 hermes_guidance_dismissed 数组
  343 |     const dismissed = await page.evaluate(() => {
  344 |       return localStorage.getItem('hermes_guidance_dismissed');
  345 |     });
  346 |     // dismissed 应该是包含 'user_registered' 的 JSON 数组
  347 |     const dismissedArr = dismissed ? JSON.parse(dismissed) : [];
  348 |     expect(dismissedArr.includes('user_registered')).toBeTruthy();
  349 |   });
  350 | 
  351 |   /**
  352 |    * 测试: 并发触发多个引导事件
  353 |    * 验证至少一个引导弹窗显示（允许并发触发显示多个）
  354 |    */
  355 |   test('并发触发多个引导事件应至少显示一个弹窗', async ({ page }) => {
  356 |     // 并发触发多个事件
  357 |     await page.evaluate(() => {
  358 |       if (window.triggerGuidance) {
  359 |         window.triggerGuidance('USER_REGISTERED', { teams: [], isFirstUser: true });
  360 |         window.triggerGuidance('TEAM_JOINED', { isFirstJoin: true });
  361 |         window.triggerGuidance('FIRST_FILE_UPLOADED', { uploadCount: 1 });
  362 |       }
  363 |     });
  364 | 
  365 |     await page.waitForTimeout(500);
  366 | 
  367 |     // 验证至少一个弹窗显示（并发触发可能显示多个，这是预期行为）
  368 |     const modalCount = await page.locator('.guidance-modal-overlay').count();
> 369 |     expect(modalCount).toBeGreaterThan(0);
      |                        ^ Error: expect(received).toBeGreaterThan(expected)
  370 |   });
  371 | });
  372 | 
```