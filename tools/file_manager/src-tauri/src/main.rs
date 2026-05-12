#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::env;
use std::process::Command;
use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    AppHandle, Emitter, Manager, WindowEvent,
};
use tracing::info;
use tracing_subscriber::{fmt, EnvFilter};

const PYTHON_API_URL: &str = "http://localhost:8080";

fn get_storage_root() -> String {
    env::var("HERMES_STORAGE_ROOT")
        .or_else(|_| env::var("HFM_STORAGE_ROOT"))
        .unwrap_or_else(|_| {
            let home = env::var("HOME").unwrap_or_default();
            format!("{}/.hermes/file_manager/storage", home)
        })
}

#[tauri::command]
async fn get_system_status() -> Result<serde_json::Value, String> {
    use serde_json::json;
    let python_status = reqwest::get(format!("{}/health", PYTHON_API_URL)).await.map(|r| r.status().is_success()).unwrap_or(false);
    Ok(json!({"python_api": python_status, "storage": {"backend": "filesystem", "root": get_storage_root()}}))
}

#[tauri::command]
fn ping() -> String {
    "pong".to_string()
}

#[tauri::command]
fn get_build_info() -> serde_json::Value {
    // 尝试读取 VERSION.json 获取完整版本信息
    // 优先使用 vue.html 入口的路径结构
    let version_info: Option<serde_json::Value> = std::fs::read_to_string("_up_/web/dist/vue.html")
        .or_else(|_| std::fs::read_to_string("_up_/web/dist/VERSION.json"))
        .or_else(|_| std::fs::read_to_string("/Applications/Hermes File Manager.app/Contents/Resources/_up_/web/dist/vue.html"))
        .or_else(|_| std::fs::read_to_string("/Applications/Hermes File Manager.app/Contents/Resources/_up_/web/dist/VERSION.json"))
        .ok()
        .and_then(|content| serde_json::from_str(&content).ok())
        .or_else(|| {
            // 尝试直接解析 VERSION.json
            std::fs::read_to_string("_up_/web/dist/VERSION.json")
                .or_else(|_| std::fs::read_to_string("/Applications/Hermes File Manager.app/Contents/Resources/_up_/web/dist/VERSION.json"))
                .ok()
                .and_then(|c| serde_json::from_str(&c).ok())
        });

    let (cargo_version, content_hash, version_string) = if let Some(info) = version_info {
        (
            info.get("cargo_version").and_then(|v| v.as_str()).unwrap_or(env!("CARGO_PKG_VERSION")).to_string(),
            info.get("content_hash").and_then(|v| v.as_str()).unwrap_or("unknown").to_string(),
            info.get("version_string").and_then(|v| v.as_str()).unwrap_or(env!("CARGO_PKG_VERSION")).to_string(),
        )
    } else {
        (
            env!("CARGO_PKG_VERSION").to_string(),
            "not_available".to_string(),
            env!("CARGO_PKG_VERSION").to_string(),
        )
    };

    serde_json::json!({
        "build_type": if cfg!(debug_assertions) { "Debug" } else { "Release" },
        "cargo_version": cargo_version,
        "content_hash": content_hash,
        "version_string": version_string,
    })
}

#[tauri::command]
async fn open_path_in_finder(path: String) -> Result<(), String> {
    let storage_root = get_storage_root();
    let full_path = if path.starts_with('/') { format!("{}/{}", storage_root, path.trim_start_matches('/')) } else { format!("{}/{}", storage_root, path) };
    #[cfg(target_os = "macos")]
    { Command::new("open").arg(&full_path).spawn().map_err(|e| e.to_string())?; }
    #[cfg(target_os = "windows")]
    { Command::new("explorer").arg(&full_path).spawn().map_err(|e| e.to_string())?; }
    #[cfg(not(any(target_os = "macos", target_os = "windows")))]
    { return Err("Unsupported platform".to_string()); }
    Ok(())
}

#[tauri::command]
async fn toggle_window(app: AppHandle, label: String) -> Result<(), String> {
    if let Some(window) = app.get_webview_window(&label) {
        if window.is_visible().unwrap_or(false) {
            window.hide().map_err(|e| e.to_string())?;
        } else {
            window.show().map_err(|e| e.to_string())?;
            window.set_focus().map_err(|e| e.to_string())?;
        }
    }
    Ok(())
}

#[tauri::command]
async fn switch_window(app: AppHandle) -> Result<(), String> {
    if app.get_webview_window("main").map(|w| w.is_visible().unwrap_or(false)).unwrap_or(false) {
        app.get_webview_window("floating").map(|w| { let _ = w.show(); let _ = w.set_focus(); });
        app.get_webview_window("main").map(|w| { let _ = w.hide(); });
    } else {
        app.get_webview_window("main").map(|w| { let _ = w.show(); let _ = w.set_focus(); });
        app.get_webview_window("floating").map(|w| { let _ = w.hide(); });
    }
    Ok(())
}

#[tauri::command]
async fn toggle_floating_window(app: AppHandle) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("floating") {
        if window.is_visible().unwrap_or(false) { window.hide().map_err(|e| e.to_string())?; }
        else { window.show().map_err(|e| e.to_string())?; window.set_focus().map_err(|e| e.to_string())?; }
    }
    Ok(())
}

#[tauri::command]
async fn emit_event(app: AppHandle, name: String, payload: String) -> Result<(), String> {
    app.emit(&name, payload).map_err(|e| e.to_string())
}

#[tauri::command]
async fn open_llm_wiki() -> Result<(), String> {
    let url = "http://127.0.0.1:19827";

    // 检查端口是否已监听（服务是否已运行）
    let port_in_use = std::net::TcpListener::bind("127.0.0.1:19827").is_err();

    if !port_in_use {
        // 服务未运行，先启动 LLM Wiki
        #[cfg(target_os = "macos")]
        {
            info!("Starting LLM Wiki service...");
            // 使用 open -a 启动 macOS 应用
            Command::new("open")
                .args(["-a", "LLM Wiki"])
                .spawn()
                .map_err(|e| e.to_string())?;

            // 等待服务启动（最多 10 秒，每 500ms 检查一次）
            for i in 0..20 {
                tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
                if std::net::TcpListener::bind("127.0.0.1:19827").is_err() {
                    info!("LLM Wiki service started successfully");
                    break;
                }
                if i == 19 {
                    return Err("LLM Wiki 服务启动超时".to_string());
                }
            }
        }
        #[cfg(target_os = "windows")]
        {
            info!("Starting LLM Wiki service...");
            // Windows: 使用 cmd start 启动应用
            Command::new("cmd")
                .args(["/c", "start", "", "LLM Wiki FM.exe"])
                .spawn()
                .map_err(|e| e.to_string())?;

            // 等待服务启动
            for i in 0..20 {
                tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
                if std::net::TcpListener::bind("127.0.0.1:19827").is_err() {
                    info!("LLM Wiki service started successfully");
                    break;
                }
                if i == 19 {
                    return Err("LLM Wiki 服务启动超时".to_string());
                }
            }
        }
        #[cfg(not(any(target_os = "macos", target_os = "windows")))]
        {
            return Err("Unsupported platform".to_string());
        }
    }

    // 打开浏览器
    #[cfg(target_os = "macos")]
    { Command::new("open").arg(url).spawn().map_err(|e| e.to_string())?; }
    #[cfg(target_os = "windows")]
    { Command::new("cmd").args(["/c", "start", url]).spawn().map_err(|e| e.to_string())?; }

    Ok(())
}

fn main() {
    let filter = EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info"));
    fmt().with_env_filter(filter).init();
    info!("Starting Hermes File Manager...");

    let app = tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_store::Builder::new().build())
        .setup(|app| {
            info!("Setting up Tauri application...");

            // 窗口由 tauri.conf.json 定义，无需代码创建

            let show_item = MenuItem::with_id(app, "show", "显示/隐藏主窗口", true, None::<&str>)?;
            let floating_item = MenuItem::with_id(app, "floating", "显示/隐藏浮窗", true, None::<&str>)?;
            let wiki_item = MenuItem::with_id(app, "wiki", "打开/关闭知识库", true, None::<&str>)?;
            let quit_wiki_item = MenuItem::with_id(app, "quit_wiki", "退出知识库", true, None::<&str>)?;
            let quit_item = MenuItem::with_id(app, "quit", "退出Hermes File Manager", true, None::<&str>)?;
            let quit_all_item = MenuItem::with_id(app, "quit_all", "全部退出", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&show_item, &floating_item, &wiki_item, &quit_wiki_item, &quit_item, &quit_all_item])?;
            let tray_icon = app.default_window_icon().cloned().expect("窗口图标未配置，请在 tauri.conf.json 中添加 icon");
            let _tray = TrayIconBuilder::new()
                .icon(tray_icon)
                .menu(&menu)
                .tooltip("Hermes File Manager")
                .on_menu_event(|app, event| {
                    match event.id.as_ref() {
                        // 退出Hermes File Manager（仅退出 Hermes，不影响知识库）
                        "quit" => std::process::exit(0),
                        // 全部退出：同时退出 Hermes 和知识库
                        "quit_all" => {
                            let _ = app.get_webview_window("main").map(|w| w.close());
                            let _ = app.get_webview_window("floating").map(|w| w.close());
                            #[cfg(target_os = "macos")]
                            { let _ = Command::new("killall").arg("llm-wiki").spawn(); }
                            #[cfg(target_os = "windows")]
                            { let _ = Command::new("taskkill").args(["/F", "/IM", "LLM Wiki FM.exe"]).spawn(); }
                            std::process::exit(0);
                        }
                        // 打开/关闭知识库（切换显示状态）
                        "wiki" => {
                            #[cfg(target_os = "macos")]
                            {
                                // AppleScript: 如果知识库窗口可见则隐藏，否则激活
                                let script = r#"try
    tell application "System Events"
        set wikiVisible to visible of process "LLM Wiki"
    end tell
    if wikiVisible then
        tell application "LLM Wiki" to activate
        delay 0.1
        tell application "System Events" to set visible of process "LLM Wiki" to false
    else
        tell application "LLM Wiki" to activate
    end if
on error
    tell application "LLM Wiki" to activate
end try"#;
                                let _ = Command::new("osascript")
                                    .args(["-e", script])
                                    .spawn();
                            }
                            #[cfg(target_os = "windows")]
                            {
                                let _ = Command::new("cmd").args(["/c", "start", "", "LLM Wiki FM.exe"]).spawn();
                            }
                        }
                        // 退出知识库（仅退出知识库，不影响 Hermes）
                        "quit_wiki" => {
                            #[cfg(target_os = "macos")]
                            { let _ = Command::new("killall").arg("llm-wiki").spawn(); }
                            #[cfg(target_os = "windows")]
                            { let _ = Command::new("taskkill").args(["/F", "/IM", "LLM Wiki FM.exe"]).spawn(); }
                        }
                        "show" => if let Some(w) = app.get_webview_window("main") { if w.is_visible().unwrap_or(false) { let _ = w.hide(); } else { let _ = w.show(); let _ = w.set_focus(); } }
                        "floating" => if let Some(w) = app.get_webview_window("floating") { if w.is_visible().unwrap_or(false) { let _ = w.hide(); } else { let _ = w.show(); let _ = w.set_focus(); } }
                        _ => {}
                    }
                })
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click { button: MouseButton::Left, button_state: MouseButtonState::Up, .. } = event {
                        let app = tray.app_handle();
                        if let Some(w) = app.get_webview_window("floating") { let _ = w.is_visible().unwrap_or(false) || { let _ = w.show(); let _ = w.set_focus(); true }; if w.is_visible().unwrap_or(false) { let _ = w.hide(); } }
                    }
                })
                .build(app)?;
            info!("System tray initialized");
            if let Some(w) = app.get_webview_window("main") {
                let title = format!("Hermes File Manager{}", if cfg!(debug_assertions) { " [DEBUG]" } else { "" });
                let _ = w.set_title(&title);
                let h = w.clone();
                w.on_window_event(move |event| { if let WindowEvent::CloseRequested { api, .. } = event { api.prevent_close(); let _ = h.hide(); } });
            }
            // floating window close-to-hide
            if let Some(w) = app.get_webview_window("floating") {
                let h = w.clone();
                w.on_window_event(move |event| { if let WindowEvent::CloseRequested { api, .. } = event { api.prevent_close(); let _ = h.hide(); } });
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_system_status, ping,
            open_path_in_finder, toggle_window, switch_window,
            toggle_floating_window,
            emit_event, get_build_info, open_llm_wiki,
        ])
        .build(tauri::generate_context!())
        .expect("Failed to build Tauri application");

    info!("Tauri application built successfully");
    app.run(move |_app_handle, _event| {
        // Exit handling done via window close handler and menu quit actions
    });
}
