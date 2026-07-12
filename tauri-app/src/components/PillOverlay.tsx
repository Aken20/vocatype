import { useEffect, useRef, useState } from "react";

const WS_URL = "ws://127.0.0.1:9877/api/ws";

export function PillOverlay() {
  const [isRecording, setIsRecording] = useState(false);
  const [status, setStatus] = useState("idle");
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "status") {
            setIsRecording(data.isRecording ?? false);
            if (data.state) setStatus(data.state);
          }
        } catch {}
      };

      ws.onclose = () => setTimeout(connect, 2000);
      ws.onerror = () => ws.close();
    };
    connect();
    return () => wsRef.current?.close();
  }, []);

  return (
    <div
      className="flex items-center gap-3 px-4 py-2 rounded-xl select-none"
      style={{
        background: "rgba(15, 15, 20, 0.92)",
        border: "1px solid rgba(255,255,255,0.08)",
        backdropFilter: "blur(12px)",
        WebkitAppRegion: "drag" as any,
      }}
      data-tauri-drag-region
    >
      {/* Recording indicator */}
      <div className="relative flex-shrink-0">
        <div
          className={`w-3 h-3 rounded-full transition-colors duration-200 ${
            isRecording ? "bg-red-500" : "bg-green-500"
          }`}
        />
        {isRecording && (
          <div className="absolute inset-0 w-3 h-3 rounded-full bg-red-500 animate-ping opacity-75" />
        )}
      </div>

      {/* Status text */}
      <span className="text-xs font-medium text-white/80">
        {isRecording
          ? "Recording..."
          : status === "transcribing"
            ? "Transcribing..."
            : "Ready"}
      </span>

      {/* Audio level bars */}
      {isRecording && (
        <div className="flex items-end gap-px h-4 ml-1">
          {Array.from({ length: 8 }).map((_, i) => (
            <div
              key={i}
              className="w-1 bg-red-400/60 rounded-t"
              style={{
                height: `${30 + Math.random() * 70}%`,
                animation: `pulse-bar ${0.2 + Math.random() * 0.3}s ease-in-out infinite alternate`,
              }}
            />
          ))}
        </div>
      )}

      <style>{`
        @keyframes pulse-bar {
          from { opacity: 0.4; }
          to { opacity: 1; }
        }
      `}</style>
    </div>
  );
}
