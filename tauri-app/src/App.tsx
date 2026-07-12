import { useDictationStore } from "./store/dictationStore";
import { useDictationWebSocket } from "./hooks/useDictationWebSocket";

function App() {
  useDictationWebSocket();
  const { isRecording, lastTranscription, status, lmStudioAvailable } =
    useDictationStore();

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6 select-none">
      {/* Header */}
      <div className="flex items-center gap-3 mb-8">
        <span className="text-2xl">🎙️</span>
        <h1 className="text-2xl font-bold tracking-tight">WhisperType</h1>
        <span className="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-500 font-mono">
          v0.1.0
        </span>
      </div>

      {/* Status Card */}
      <div className="mb-6 p-5 bg-gray-900 rounded-xl border border-gray-800">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm text-gray-400">Status</span>
          <div
            className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium ${
              isRecording
                ? "bg-red-500/20 text-red-400 animate-pulse"
                : status === "transcribing"
                  ? "bg-yellow-500/20 text-yellow-400"
                  : "bg-green-500/20 text-green-400"
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isRecording
                  ? "bg-red-500"
                  : status === "transcribing"
                    ? "bg-yellow-500"
                    : "bg-green-500"
              }`}
            />
            {isRecording
              ? "Recording..."
              : status === "transcribing"
                ? "Transcribing..."
                : "Ready"}
          </div>
        </div>

        {/* Audio level bar (placeholder) */}
        {isRecording && (
          <div className="flex items-end gap-0.5 h-8 mb-3">
            {Array.from({ length: 20 }).map((_, i) => (
              <div
                key={i}
                className="w-2 bg-red-500/60 rounded-t animate-pulse"
                style={{
                  height: `${20 + Math.random() * 80}%`,
                  animationDelay: `${i * 50}ms`,
                }}
              />
            ))}
          </div>
        )}

        {/* LM Studio indicator */}
        <div className="flex items-center gap-2 text-xs">
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              lmStudioAvailable ? "bg-green-500" : "bg-gray-600"
            }`}
          />
          <span className="text-gray-500">
            AI Cleanup:{" "}
            {lmStudioAvailable ? (
              <span className="text-green-400">Connected (LM Studio)</span>
            ) : (
              <span className="text-gray-500">Offline</span>
            )}
          </span>
        </div>
      </div>

      {/* Last Transcription */}
      {lastTranscription && (
        <div className="mb-6 p-4 bg-gray-900 rounded-xl border border-gray-800">
          <p className="text-xs text-gray-500 mb-2 uppercase tracking-wider">
            Last transcription
          </p>
          <p className="text-gray-200 leading-relaxed">{lastTranscription}</p>
        </div>
      )}

      {/* Hotkey Hint */}
      <div className="p-4 bg-gray-900/50 rounded-xl border border-gray-800/50">
        <p className="text-sm text-gray-500 text-center">
          Press{" "}
          <kbd className="px-2 py-0.5 bg-gray-800 rounded text-gray-300 font-mono text-xs border border-gray-700">
            Ctrl+Shift+V
          </kbd>{" "}
          to start/stop dictation
        </p>
      </div>
    </div>
  );
}

export default App;
