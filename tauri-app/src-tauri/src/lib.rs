use std::process::{Child, Command};
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

            // Resolve python-backend path relative to the project root
            let backend_dir = std::env::current_dir()
                .unwrap_or_default()
                .parent()
                .unwrap_or(std::path::Path::new("."))
                .join("python-backend");

            // In dev mode, the cwd is tauri-app/src-tauri, so go up two levels
            let backend_dir = if backend_dir.exists() {
                backend_dir
            } else {
                std::env::current_dir()
                    .unwrap_or_default()
                    .parent() // src-tauri
                    .unwrap_or(std::path::Path::new("."))
                    .parent() // tauri-app
                    .unwrap_or(std::path::Path::new("."))
                    .join("python-backend")
            };

            if backend_dir.exists() {
                let child = Command::new("python")
                    .arg("main.py")
                    .current_dir(&backend_dir)
                    .spawn();

                match child {
                    Ok(process) => {
                        log::info!(
                            "Python backend started (PID: {}) from {}",
                            process.id(),
                            backend_dir.display()
                        );
                        app.manage(PythonBackend(Mutex::new(Some(process))));
                    }
                    Err(e) => {
                        log::warn!(
                            "Could not start Python backend from {}: {}. \
                             Start it manually: cd {} && python main.py",
                            backend_dir.display(),
                            e,
                            backend_dir.display()
                        );
                        app.manage(PythonBackend(Mutex::new(None)));
                    }
                }
            } else {
                log::warn!(
                    "Python backend not found at {}. Expected: {}/python-backend/main.py",
                    backend_dir.display(),
                    std::env::current_dir().unwrap_or_default().display()
                );
                app.manage(PythonBackend(Mutex::new(None)));
            }

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                if let Some(state) = window.try_state::<PythonBackend>() {
                    if let Ok(mut guard) = state.0.lock() {
                        if let Some(ref mut child) = *guard {
                            log::info!("Shutting down Python backend (PID: {})", child.id());
                            let _ = child.kill();
                        }
                    }
                }
            }
        })
        .invoke_handler(tauri::generate_handler![get_backend_url])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
