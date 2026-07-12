import { useEffect, useRef, useCallback } from "react";
import { useDictationStore } from "../store/dictationStore";

const WS_URL = "ws://127.0.0.1:9877/api/ws";

export function useDictationWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<number | null>(null);
  const store = useDictationStore();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connected to WhisperType backend");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        switch (data.type) {
          case "status":
            if (data.isRecording) {
              store.setRecording(true);
            } else {
              store.setRecording(false);
              if (data.lastText) {
                store.setLastTranscription(data.lastText);
                store.setStatus("done");
              }
            }
            break;
          case "health":
            store.setLmStudioAvailable(data.lmStudioAvailable ?? false);
            break;
          case "error":
            console.error("Backend error:", data.message);
            break;
        }
      } catch (e) {
        console.error("Failed to parse WebSocket message:", e);
      }
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected, reconnecting in 2s...");
      reconnectTimeout.current = window.setTimeout(connect, 2000);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [store]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeout.current !== null) {
        clearTimeout(reconnectTimeout.current);
      }
      wsRef.current?.close();
    };
  }, [connect]);
}
