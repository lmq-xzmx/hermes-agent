/**
 * Platform Adapter - Tauri 平台适配器
 *
 * 提供统一的平台抽象接口：
 * - Tauri 命令调用 (invoke)
 * - 事件监听 (listen)
 * - 事件发送 (emit)
 * - API 配置
 * - WebSocket 连接
 *
 * 构建时注入的值（由 vite.config.js define）：
 * - __API_BASE__: API 基础路径
 * - __WS_BASE__: WebSocket 基础路径
 * - __TAURI_MODE__: 运行模式 ('tauri' | 'web')
 */

(function(global) {
  // 构建时注入的值
  var API_BASE = typeof __API_BASE__ !== 'undefined' ? __API_BASE__ : '/api/v1';
  var WS_BASE = typeof __WS_BASE__ !== 'undefined' ? __WS_BASE__ : 'ws://localhost:8080';
  var TAURI_MODE = typeof __TAURI_MODE__ !== 'undefined' ? __TAURI_MODE__ : 'web';

  // 运行时检测：如果 window.__TAURI__ 存在，说明在 Tauri 环境中运行
  var isTauriRuntime = typeof window.__TAURI__ !== 'undefined';

  // 如果是 Tauri 运行时但构建时没设置正确的 API_BASE，使用 localhost
  if (isTauriRuntime && API_BASE === '/api/v1') {
    API_BASE = 'http://localhost:8080/api/v1';
    WS_BASE = 'ws://localhost:8080';
  }

  /**
   * 调用 Tauri 命令
   */
  function tauriInvoke(command, args) {
    // 使用 window.__TAURI__ 检测真正的 Tauri 运行时
    if (typeof window.__TAURI__ !== 'undefined' && typeof window.__TAURI__.invoke === 'function') {
      return window.__TAURI__.invoke(command, args);
    }
    throw new Error('Tauri command "' + command + '" not available in ' + TAURI_MODE + ' mode');
  }

  /**
   * 监听 Tauri 事件
   */
  function tauriListen(eventName, callback) {
    if (window.__TAURI__ && window.__TAURI__.event && window.__TAURI__.event.listen) {
      return window.__TAURI__.event.listen(eventName, callback);
    }
    console.warn('Tauri event "' + eventName + '" not available in ' + TAURI_MODE + ' mode');
    return Promise.resolve({ unsubscribe: function() {} });
  }

  /**
   * 发送 Tauri 事件
   */
  function tauriEmit(eventName, payload) {
    if (window.__TAURI__ && window.__TAURI__.core && window.__TAURI__.core.emit) {
      return window.__TAURI__.core.emit(eventName, payload);
    }
    console.warn('Tauri emit "' + eventName + '" not available in ' + TAURI_MODE + ' mode');
    return Promise.resolve(false);
  }

  // 平台适配器对象
  var platform = {
    api: {
      base: API_BASE,
      wsBase: WS_BASE,
      isTauri: TAURI_MODE === 'tauri',
      mode: TAURI_MODE,
      getSystemStatus: function() { return tauriInvoke('get_system_status'); },
      getBuildInfo: function() { return tauriInvoke('get_build_info'); },
      openPath: function(path) { return tauriInvoke('open_path_in_finder', { path: path }); },
      toggleWindow: function(label) { return tauriInvoke('toggle_window', { label: label }); },
      switchWindow: function() { return tauriInvoke('switch_window'); },
      openLlmWiki: function() { return tauriInvoke('open_llm_wiki'); },
      emitEvent: function(name, payload) { return tauriInvoke('emit_event', { name: name, payload: JSON.stringify(payload) }); },
    },
    ws: {
      base: WS_BASE,
      connect: function(token, onMessage) {
        var wsUrl = WS_BASE + '/ws/admin/analytics?token=' + token;
        var socket = new WebSocket(wsUrl);
        socket.onopen = function() { console.log('[Platform WS] Connected'); setInterval(function() { if (socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ type: 'ping' })); }, 30000); };
        socket.onmessage = function(event) { try { var data = JSON.parse(event.data); if (onMessage) onMessage(data); } catch (e) { console.warn('[Platform WS] Failed to parse message:', e); } };
        socket.onclose = function() { console.log('[Platform WS] Disconnected'); };
        socket.onerror = function(error) { console.error('[Platform WS] Error:', error); };
        return socket;
      },
    },
    platform: {
      isTauri: TAURI_MODE === 'tauri',
      mode: TAURI_MODE,
      openUrl: function(url) { window.open(url, '_blank'); },
      listen: tauriListen,
      emit: tauriEmit,
    },
    invoke: tauriInvoke,
    listen: tauriListen,
    emit: tauriEmit,
  };

  // 暴露到全局
  global.platform = platform;
  global.API_BASE = API_BASE;
  global.WS_BASE = WS_BASE;
  // 注意：不设置 global.tauri，避免与 Tauri 运行时的 window.__TAURI__ 冲突
  // 如果 Tauri 运行时将 window.__TAURI__ 指向我们的 tauri 对象，
  // 会导致 tauriInvoke 调用 window.__TAURI__.invoke 时递归调用自己
  // __TAURI_INVOKE__ 总是设置，因为我们的 tauriInvoke 有 Fallback 逻辑
  global.__TAURI_INVOKE__ = tauriInvoke;

  console.log('[Platform Adapter] Initialized in ' + (isTauriRuntime ? 'TAURI' : TAURI_MODE) + ' mode, API_BASE=' + API_BASE);
})(window);
