import { create } from "zustand";

export type DictationStatus = "idle" | "recording" | "transcribing" | "done";

interface DictationState {
  isRecording: boolean;
  lastTranscription: string;
  status: DictationStatus;
  lmStudioAvailable: boolean;
  // Actions
  setRecording: (recording: boolean) => void;
  setLastTranscription: (text: string) => void;
  setStatus: (status: DictationStatus) => void;
  setLmStudioAvailable: (available: boolean) => void;
}

export const useDictationStore = create<DictationState>((set) => ({
  isRecording: false,
  lastTranscription: "",
  status: "idle",
  lmStudioAvailable: false,
  setRecording: (recording) =>
    set({
      isRecording: recording,
      status: recording ? "recording" : "idle",
    }),
  setLastTranscription: (text) => set({ lastTranscription: text }),
  setStatus: (status) => set({ status }),
  setLmStudioAvailable: (available) => set({ lmStudioAvailable: available }),
}));
