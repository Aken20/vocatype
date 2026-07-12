import { useEffect, useRef, useCallback } from "react";
import { useDictationStore } from "../store/dictationStore";

const WS_URL = "ws://127.0.0.1:9877/api/ws";

export function useDictationWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<number | null>(null);
  const store = useDictationStore();

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
        switch (data.type) {
          case "status":
            store.setRecording(data.isRecording ?? false);
            if (data.lastText) store.setLastTranscription(data.lastText);
            if (data.state) store.setStatus(data.state);
            break;
          case "health":
            store.setLmStudioAvailable(data.lmStudioAvailable ?? false);
            break;
        }
      } catch {}
    };

    ws.onclose = () => {
      reconnectTimeout.current = window.setTimeout(connect, 2000);
    };

    ws.onerror = () => ws.close();
  }, [store]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { ws: wsRef, sendAction };
}
