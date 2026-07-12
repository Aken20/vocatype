import { useEffect, useRef, useCallback } from "react";
import { useDictationStore } from "../store/dictationStore";

const WS_URL = "ws://127.0.0.1:9877/api/ws";

export function useDictationWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<number | null>(null);

  const sendAction = useCallback((action: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action }));
    }
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => console.log("WS connected");

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const s = useDictationStore.getState();
        switch (data.type) {
          case "status":
            if (data.isRecording !== undefined) s.setRecording(data.isRecording);
            if (data.lastText) s.setLastTranscription(data.lastText);
            if (data.state) s.setStatus(data.state);
            break;
          case "health":
            s.setLmStudioAvailable(data.lmStudioAvailable ?? false);
            break;
        }
      } catch { /* ignore parse errors */ }
    };

    ws.onclose = () => {
      reconnectTimeout.current = window.setTimeout(connect, 2000);
    };

    ws.onerror = () => ws.close();
  }, []); // stable — uses getState(), doesn't depend on store ref

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { ws: wsRef, sendAction };
}
