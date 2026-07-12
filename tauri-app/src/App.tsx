import { useCallback } from "react";
import { useDictationStore } from "./store/dictationStore";
import { useDictationWebSocket } from "./hooks/useDictationWebSocket";

const API = "http://127.0.0.1:9877";

function App() {
  const { ws, sendAction } = useDictationWebSocket();
  const { isRecording, lastTranscription, status, lmStudioAvailable } =
    useDictationStore();

  const toggleDictation = useCallback(async () => {
    if (isRecording) {
      sendAction("stop");
    } else {
      sendAction("start");
    }
  }, [isRecording, sendAction]);

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6 flex flex-col gap-5 select-none">
      {/* Header */}
      <div className="flex items-center gap-3">
        <span className="text-2xl">🎙️</span>
        <h1 className="text-xl font-bold tracking-tight">WhisperType</h1>
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-800 text-gray-500 font-mono">
          v0.1
        </span>
      </div>

      {/* Dictation Button */}
      <button
        onClick={toggleDictation}
        className={`w-full py-8 rounded-2xl text-lg font-semibold transition-all duration-200 cursor-pointer border-2 ${
          isRecording
            ? "bg-red-600/30 border-red-500 text-red-300 animate-pulse"
            : status === "transcribing"
              ? "bg-yellow-600/20 border-yellow-600 text-yellow-300"
              : "bg-violet-600/20 border-violet-600 text-violet-300 hover:bg-violet-600/30"
        }`}
      >
        {isRecording
          ? "⏹ Stop Dictation"
          : status === "transcribing"
            ? "⏳ Transcribing..."
            : "🎤 Start Dictation"}
      </button>

      {/* Audio meter (placeholder) */}
      {isRecording && (
        <div className="flex items-end gap-0.5 h-8">
          {Array.from({ length: 24 }).map((_, i) => (
            <div
              key={i}
              className="flex-1 bg-red-500/50 rounded-t transition-all"
              style={{
                height: `${15 + Math.random() * 85}%`,
                animation: `pulse ${0.3 + Math.random() * 0.5}s ease-in-out infinite alternate`,
              }}
            />
          ))}
        </div>
      )}

      {/* Status bar */}
      <div className="flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${
              isRecording ? "bg-red-500" : "bg-green-500"
            }`}
          />
          {isRecording ? "Recording" : "Ready"}
        </div>
        <div className="flex items-center gap-1.5">
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              lmStudioAvailable ? "bg-green-500" : "bg-gray-600"
            }`}
          />
          {lmStudioAvailable ? "AI Cleanup On" : "AI Cleanup Offline"}
        </div>
      </div>

      {/* Last Transcription */}
      {lastTranscription && (
        <div className="p-4 bg-gray-900 rounded-xl border border-gray-800">
          <p className="text-[10px] text-gray-500 mb-1 uppercase tracking-wider">
            Last transcription
          </p>
          <p className="text-gray-200 text-sm leading-relaxed">
            {lastTranscription}
          </p>
        </div>
      )}

      {/* Hotkey */}
      <div className="mt-auto pt-4 text-center">
        <p className="text-xs text-gray-600">
          Hotkey:{" "}
          <kbd className="px-1.5 py-0.5 bg-gray-800 rounded text-gray-400 font-mono text-[10px] border border-gray-700">
            Ctrl+Shift+.
          </kbd>
        </p>
      </div>
    </div>
  );
}

export default App;
