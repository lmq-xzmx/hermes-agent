#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::env;
use std::process::Command;
use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    AppHandle, Emitter, Manager, RunEvent, WindowEvent,
};
use tracing::info;
use tracing_subscriber::{fmt, EnvFilter};

const PYTHON_API_URL: &str = "http://localhost:8080";
const LLM_WIKI_SERVE_PORT: u16 = 19827;

fn get_storage_root() -> String {
    env::var("HERMES_STORAGE_ROOT")
        .or_else(|_| env::var("HFM_STORAGE_ROOT"))
        .unwrap_or_else(|_| {
            let home = env::var("HOME").unwrap_or_default();
            format!("{}/.hermes/file_manager/storage", home)
        })
}

fn get_llm_wiki_bundle() -> Option<std::path::PathBuf> {
    let candidates = vec![
        std::path::PathBuf::from("/Applications/LLM Wiki FM.app"),
        std::path::PathBuf::from("./llm_wiki_FM/target/release/bundle/macos/LLM Wiki FM.app"),
        std::env::current_dir().ok()?.join("llm_wiki_FM/target/release/bundle/macos/LLM Wiki FM.app"),
    ];
    for candidate in candidates {
        if candidate.exists() {
            return Some(candidate);
        }
    }
    None
}

fn spawn_llm_wiki_gui() -> Result<(), String> {
    if let Some(bundle) = get_llm_wiki_bundle() {
        Command::new("open").arg("-a").arg(&bundle).spawn().map_err(|e| format!("Failed to open LLM Wiki: {}", e))?;
        Ok(())
    } else {
        Err("LLM Wiki bundle not found".to_string())
    }
}

#[tauri::command]
async fn get_python_api_status() -> Result<String, String> {
    let url = format!("{}/health", PYTHON_API_URL);
    match reqwest::get(&url).await {
        Ok(resp) => {
            if resp.status().is_success() {
                Ok("running".to_string())
            } else {
                Err(format!("API returned status: {}", resp.status()))
            }
        }
        Err(e) => Err(format!("Failed to connect to API: {}", e)),
    }
}

#[tauri::command]
async fn get_system_status() -> Result<serde_json::Value, String> {
    use serde_json::json;
    let python_status = reqwest::get(format!("{}/health", PYTHON_API_URL)).await.map(|resp| resp.status().is_success()).unwrap_or(false);
    let llm_wiki_status = reqwest::get(format!("http://localhost:{}/health", LLM_WIKI_SERVE_PORT)).await.map(|resp| resp.status().is_success()).unwrap_or(false);
    Ok(json!({"python_api": python_status, "llm_wiki": llm_wiki_status, "storage": {"backend": "filesystem", "root": get_storage_root()}}))
}

#[tauri::command]
async fn open_llm_wiki() -> Result<(), String> {
    let is_running = reqwest::get(format!("http://localhost:{}/health", LLM_WIKI_SERVE_PORT)).await.is_ok();
    if is_running {
        Command::new("pkill").arg("-f").arg("llm-wiki-fm").spawn().map_err(|e| e.to_string())?;
        Ok(())
    } else {
        Err("LLM Wiki not running".to_string())
    }
}

#[tauri::command]
fn ping() -> String {
    "pong".to_string()
}

#[tauri::command]
async fn get_llm_wiki_status() -> Result<bool, String> {
    reqwest::get(format!("http://localhost:{}/health", LLM_WIKI_SERVE_PORT)).await.map(|resp| resp.status().is_success()).map_err(|e| e.to_string())
}

#[tauri::command]
async fn launch_hermes() -> Result<(), String> {
    spawn_llm_wiki_gui()
}

#[tauri::command]
async fn open_path_in_finder(path: String) -> Result<(), String> {
    info!("Opening in finder: {}", path);
    let storage_root = get_storage_root();
    let full_path = if path.starts_with('/') {
        format!("{}/{}", storage_root, path.trim_start_matches('/'))
    } else {
        format!("{}/{}", storage_root, path)
    };
    info!("Full path: {}", full_path);
    #[cfg(target_os = "macos")]
    {
        Command::new("open").arg(&full_path).spawn().map_err(|e| format!("Failed to open in finder: {}", e))?;
    }
    #[cfg(target_os = "windows")]
    {
        Command::new("explorer").arg(&full_path).spawn().map_err(|e| format!("Failed to open in explorer: {}", e))?;
    }
    #[cfg(not(any(target_os = "macos", target_os = "windows")))]
    {
        return Err("Open in finder is only supported on macOS and Windows".to_string());
    }
    Ok(())
}

#[tauri::command]
async fn show_floating_window(app: AppHandle) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("floating") {
        window.show().map_err(|e| e.to_string())?;
        window.set_focus().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
async fn hide_floating_window(app: AppHandle) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("floating") {
        window.hide().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
async fn show_main_window(app: AppHandle) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("main") {
        window.show().map_err(|e| e.to_string())?;
        window.set_focus().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
async fn quick_upload(app: AppHandle) -> Result<(), String> {
    app.emit("quick-upload", ()).map_err(|e| e.to_string())?;
    if let Some(window) = app.get_webview_window("main") {
        window.show().map_err(|e| e.to_string())?;
        window.set_focus().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
async fn show_space_usage(app: AppHandle) -> Result<(), String> {
    app.emit("show-space-usage", ()).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
async fn focus_search(app: AppHandle) -> Result<(), String> {
    app.emit("focus-search", ()).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
async fn open_recent_file(app: AppHandle, filename: String) -> Result<(), String> {
    app.emit("open-recent-file", filename).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
async fn open_settings(app: AppHandle) -> Result<(), String> {
    app.emit("open-settings", ()).map_err(|e| e.to_string())?;
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
            if let Some(window) = app.get_webview_window("floating") {
                info!("Floating window exists, label: {:?}", window.label());
            } else {
                info!("Floating window not found, it will be created from tauri.conf.json");
            }
            let show_item = MenuItem::with_id(app, "show", "显示/隐藏主窗口", true, None::<&str>)?;
            let floating_item = MenuItem::with_id(app, "floating", "显示/隐藏浮窗", true, None::<&str>)?;
            let open_llm_wiki_item = MenuItem::with_id(app, "open_llm_wiki", "打开/关闭知识库", true, None::<&str>)?;
            let quit_hermes_item = MenuItem::with_id(app, "quit_hermes", "退出 Hermes File Manager", true, None::<&str>)?;
            let quit_both_item = MenuItem::with_id(app, "quit_both", "退出全部", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&show_item, &floating_item, &open_llm_wiki_item, &quit_hermes_item, &quit_both_item])?;
            let tray_icon = app.default_window_icon().cloned().expect("窗口图标未配置，请在 tauri.conf.json 中添加 icon");
            let _tray = TrayIconBuilder::new()
                .icon(tray_icon)
                .menu(&menu)
                .tooltip("Hermes File Manager")
                .on_menu_event(|app, event| {
                    match event.id.as_ref() {
                        "show" => {
                            if let Some(window) = app.get_webview_window("main") {
                                if window.is_visible().unwrap_or(false) {
                                    let _ = window.hide();
                                } else {
                                    let _ = window.show();
                                    let _ = window.set_focus();
                                }
                            }
                        }
                        "floating" => {
                            info!("Floating menu clicked, getting floating window");
                            if let Some(window) = app.get_webview_window("floating") {
                                info!("Found floating window, label: {:?}", window.label());
                                if window.is_visible().unwrap_or(false) {
                                    info!("Hiding floating window");
                                    let _ = window.hide();
                                } else {
                                    info!("Showing floating window");
                                    let _ = window.show();
                                    let _ = window.set_focus();
                                }
                            } else {
                                info!("Floating window NOT found!");
                            }
                        }
                        "open_llm_wiki" => {
                            let rt = tokio::runtime::Runtime::new().unwrap();
                            let is_running = rt.block_on(async {
                                reqwest::get(format!("http://localhost:{}/health", LLM_WIKI_SERVE_PORT)).await.is_ok()
                            });
                            if is_running {
                                let _ = Command::new("pkill").arg("-f").arg("llm-wiki-fm").spawn();
                                info!("LLM Wiki GUI closed");
                            } else {
                                let _ = spawn_llm_wiki_gui();
                            }
                        }
                        "quit_hermes" => {
                            info!("Quit Hermes requested");
                            std::process::exit(0);
                        }
                        "quit_both" => {
                            let _ = Command::new("pkill").arg("-f").arg("llm-wiki-fm").spawn();
                            info!("Quitting both Hermes and LLM Wiki");
                            std::process::exit(0);
                        }
                        _ => {}
                    }
                })
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click { button: MouseButton::Left, button_state: MouseButtonState::Up, .. } = event {
                        let app = tray.app_handle();
                        if let Some(window) = app.get_webview_window("floating") {
                            if window.is_visible().unwrap_or(false) {
                                let _ = window.hide();
                            } else {
                                let _ = window.show();
                                let _ = window.set_focus();
                            }
                        }
                    }
                })
                .build(app)?;
            info!("System tray initialized");
            if let Some(main_window) = app.get_webview_window("main") {
                let window_handle = main_window.clone();
                main_window.on_window_event(move |event| {
                    if let WindowEvent::CloseRequested { api, .. } = event {
                        api.prevent_close();
                        let _ = window_handle.hide();
                    }
                });
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_python_api_status, get_system_status, open_llm_wiki, ping, get_llm_wiki_status, launch_hermes,
            open_path_in_finder, show_floating_window, hide_floating_window, show_main_window,
            quick_upload, show_space_usage, focus_search, open_recent_file, open_settings,
        ])
        .build(tauri::generate_context!())
        .expect("Failed to build Tauri application");

    info!("Tauri application built successfully");
    app.run(move |_app_handle, _event| {
        // Exit handling done via window close handler and menu quit actions
    });
}
