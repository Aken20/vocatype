use std::process::Child;
use std::sync::Mutex;
use tauri::Manager;

struct PythonBackend(Mutex<Option<Child>>);

#[tauri::command]
fn get_backend_url() -> String {
    "http://127.0.0.1:9877".to_string()
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

            // In dev mode, start Python manually in a separate terminal.
            // Tauri only hosts the UI — no auto-spawn to avoid port conflicts.
            app.manage(PythonBackend(Mutex::new(None)));

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![get_backend_url])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
