use std::process::Child;
use std::sync::Mutex;
use tauri::Manager;

struct PythonBackend(Mutex<Option<Child>>);

#[tauri::command]
fn get_backend_url() -> String {
    "http://127.0.0.1:9877".to_string()
}

#[tauri::command]
fn toggle_pill(app: tauri::AppHandle) -> Result<String, String> {
    let label = "pill";
    if let Some(w) = app.get_webview_window(label) {
        w.close().map_err(|e| e.to_string())?;
        Ok("closed".into())
    } else {
        let w = tauri::WebviewWindowBuilder::new(
            &app,
            label,
            tauri::WebviewUrl::App("/#pill".into()),
        )
        .title("VocaType Pill")
        .inner_size(280.0, 48.0)
        .resizable(false)
        .decorations(false)
        .always_on_top(true)
        .skip_taskbar(true)
        .visible_on_all_workspaces(true)
        .build()
        .map_err(|e| e.to_string())?;

        // Position bottom-right
        if let Some(monitor) = app.primary_monitor().map_err(|e| e.to_string())? {
            let size = monitor.size();
            let pos = (size.width as f64 - 292.0, size.height as f64 - 80.0);
            w.set_position(tauri::Position::Physical(
                tauri::PhysicalPosition::new(pos.0 as i32, pos.1 as i32),
            ))
            .map_err(|e| e.to_string())?;
        }

        Ok("opened".into())
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            app.manage(PythonBackend(Mutex::new(None)));
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![get_backend_url, toggle_pill])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
