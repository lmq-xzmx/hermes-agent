/**
 * Tauri Platform Adapter
 *
 * 提供 Tauri 命令调用接口，包含 open_llm_wiki 的 Fallback 逻辑
 * 使用 import.meta.env 获取 Vite 注入的环境变量
 */

// Vite 注入的环境变量
var API_BASE = import.meta.env.VITE_API_BASE || '/api/v1';
var WS_BASE = import.meta.env.VITE_WS_BASE || 'ws://localhost:8080';
var TAURI_MODE = import.meta.env.VITE_TAURI_MODE || 'web';

// 运行时检测：如果 window.__TAURI__ 存在，说明在 Tauri 环境中运行
var isTauriRuntime = typeof window.__TAURI__ !== 'undefined';

if (isTauriRuntime && API_BASE === '/api/v1') {
  API_BASE = 'http://localhost:8080/api/v1';
  WS_BASE = 'ws://localhost:8080';
}

function tauriInvoke(command, args) {
  console.log('[tauriInvoke] command:', command, 'args:', args);

  // Tauri v2 检测：window.__TAURI__ 存在（withGlobalTauri: true）或通过 import 检测
  var hasTauri = typeof window.__TAURI__ !== 'undefined' && window.__TAURI__ !== null;

  // 如果是 open_llm_wiki 且没有 Tauri 环境，直接用浏览器打开
  if (command === 'open_llm_wiki') {
    if (hasTauri && typeof window.__TAURI__.invoke === 'function') {
      console.log('[tauriInvoke] using window.__TAURI__.invoke');
      return window.__TAURI__.invoke(command, args);
    }
    // Tauri v2: 使用 @tauri-apps/api/core 的 invoke
    if (typeof window !== 'undefined' && window.__TAURI_INVOKE__) {
      console.log('[tauriInvoke] using window.__TAURI_INVOKE__');
      return window.__TAURI_INVOKE__(command, args);
    }
    // Fallback: 直接打开 URL
    console.log('[tauriInvoke] using window.open fallback');
    window.open('http://localhost:19827', '_blank');
    return Promise.resolve();
  }

  // 其他命令
  if (hasTauri && typeof window.__TAURI__.invoke === 'function') {
    return window.__TAURI__.invoke(command, args);
  }
  if (typeof window.__TAURI_INVOKE__ === 'function') {
    return window.__TAURI_INVOKE__(command, args);
  }
  throw new Error('Tauri command "' + command + '" not available in ' + TAURI_MODE + ' mode');
}

function tauriListen(eventName, callback) {
  if (window.__TAURI__ && window.__TAURI__.event && window.__TAURI__.event.listen) {
    return window.__TAURI__.event.listen(eventName, callback);
  }
  console.warn('Tauri event "' + eventName + '" not available in ' + TAURI_MODE + ' mode');
  return Promise.resolve({ unsubscribe: function() {} });
}

function tauriEmit(eventName, payload) {
  if (window.__TAURI__ && window.__TAURI__.core && window.__TAURI__.core.emit) {
    return window.__TAURI__.core.emit(eventName, payload);
  }
  console.warn('Tauri emit "' + eventName + '" not available in ' + TAURI_MODE + ' mode');
  return Promise.resolve(false);
}

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
window.platform = platform;
window.API_BASE = API_BASE;
window.WS_BASE = WS_BASE;
window.__TAURI_INVOKE__ = tauriInvoke;

console.log('[Platform Adapter] Initialized in ' + (isTauriRuntime ? 'TAURI' : TAURI_MODE) + ' mode, API_BASE=' + API_BASE);
