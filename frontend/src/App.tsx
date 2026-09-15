import { useEffect, useRef, useState } from "react";
import LandingPage from "./Landingpage";
import { DOMAINS } from "./Domains";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "https://aptigrad.onrender.com";

type Screen = "landing" | "lobby" | "interview";
type PermissionState = "idle" | "checking" | "granted" | "denied";
type CallStatus = "ready" | "listening" | "analyzing" | "speaking" | "error";

function pickAudioMimeType(): string {
  const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/mp4"];
  if (typeof MediaRecorder === "undefined") return "";
  for (const type of candidates) {
    if (MediaRecorder.isTypeSupported(type)) return type;
  }
  return "";
}

const IconCamera = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="6" width="13" height="12" rx="2" />
    <path d="M16 10.5 21 7v10l-5-3.5" />
  </svg>
);
const IconMic = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="9" y="3" width="6" height="11" rx="3" />
    <path d="M5 11a7 7 0 0 0 14 0" />
    <path d="M12 18v3" />
    <path d="M8.5 21h7" />
  </svg>
);
const IconStop = () => (
  <svg viewBox="0 0 24 24" fill="currentColor">
    <rect x="6" y="6" width="12" height="12" rx="2" />
  </svg>
);
const IconSpeaker = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 9v6h4l5 4V5L8 9H4Z" />
    <path d="M16.5 8.5a5 5 0 0 1 0 7" />
  </svg>
);
const IconSpeakerMute = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 9v6h4l5 4V5L8 9H4Z" />
    <path d="M17 9l4 6M21 9l-4 6" />
  </svg>
);
const IconEndCall = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3.5 13c5-4.5 12-4.5 17 0" />
    <path d="M9 15.5l1.6-1.8a2 2 0 0 1 2.8 0L15 15.5" />
    <path d="M4 13l2.2 2.6M20 13l-2.2 2.6" />
  </svg>
);
const IconLock = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="5" y="10" width="14" height="10" rx="2" />
    <path d="M8 10V7a4 4 0 0 1 8 0v3" />
  </svg>
);
const IconCheck = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M5 12.5l4.5 4.5L19 7" />
  </svg>
);
const IconAlert = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 3.5 21.5 20h-19L12 3.5Z" />
    <path d="M12 9.5v4.2M12 17h.01" />
  </svg>
);

const GLOBAL_STYLES = `
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

.apg-app, .apg-app *, .apg-app *::before, .apg-app *::after { box-sizing: border-box; }

.apg-app {
  --apg-bg: #F5F6F8;
  --apg-surface: #FFFFFF;
  --apg-ink: #10151F;
  --apg-ink-soft: #5B6472;
  --apg-line: #E2E5EA;
  --apg-navy: #0F1B2D;
  --apg-navy-soft: #1C2C46;
  --apg-gold: #E8A33D;
  --apg-teal: #1F8A63;
  --apg-red: #C23B3B;
  --apg-r-lg: 20px;
  --apg-r-md: 14px;
  --apg-r-sm: 10px;
  font-family: 'Inter', system-ui, sans-serif;
  color: var(--apg-ink);
  min-height: 100vh;
}

.apg-app button { font-family: inherit; }
.apg-app :focus-visible { outline: 2px solid var(--apg-gold); outline-offset: 2px; }

.apg-lobby { min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 32px 20px; background: var(--apg-bg); }
.apg-lobby-card { width: 100%; max-width: 960px; background: var(--apg-surface); border: 1px solid var(--apg-line); border-radius: var(--apg-r-lg); overflow: hidden; display: grid; grid-template-columns: 1.05fr 1fr; box-shadow: 0 30px 70px -40px rgba(15,27,45,0.4); animation: apg-rise 0.5s ease both; }
@media (max-width: 820px) { .apg-lobby-card { grid-template-columns: 1fr; } }

.apg-lobby-preview { background: var(--apg-navy); min-height: 380px; position: relative; display: flex; align-items: center; justify-content: center; overflow: hidden; }
.apg-lobby-video { width: 100%; height: 100%; object-fit: cover; position: absolute; inset: 0; }
.apg-preview-empty { color: rgba(255,255,255,0.6); text-align: center; padding: 32px; display: flex; flex-direction: column; align-items: center; gap: 10px; }
.apg-preview-empty svg { width: 30px; height: 30px; }
.apg-preview-empty p { margin: 0; font-size: 0.9rem; max-width: 26ch; }

.apg-meter { position: absolute; bottom: 18px; left: 18px; display: flex; align-items: flex-end; gap: 4px; height: 28px; }
.apg-meter-bar { width: 4px; height: 100%; border-radius: 2px; background: var(--apg-gold); transform-origin: bottom; transition: transform 0.08s linear; }

.apg-lobby-form { padding: 40px 36px; display: flex; flex-direction: column; gap: 26px; }

.apg-brand { display: flex; align-items: center; gap: 12px; }
.apg-brand-mark { width: 40px; height: 40px; border-radius: 50%; background: var(--apg-navy); color: var(--apg-gold); font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.15rem; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.apg-brand-mark--sm { width: 32px; height: 32px; font-size: 0.95rem; }
.apg-brand-name { margin: 0; font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 1.05rem; }
.apg-brand-name--sm { color: #fff; font-size: 0.95rem; }
.apg-brand-tag { margin: 2px 0 0; font-size: 0.8rem; color: var(--apg-ink-soft); }
.apg-brand--dark .apg-brand-tag { display: none; }

.apg-lobby-heading { margin: 0; font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 1.7rem; line-height: 1.25; }
.apg-lobby-copy { margin: 0; color: var(--apg-ink-soft); font-size: 0.95rem; line-height: 1.55; max-width: 46ch; }

.apg-field { display: flex; flex-direction: column; gap: 10px; }
.apg-field-label { font-size: 0.85rem; font-weight: 600; color: var(--apg-ink); }
.apg-chip-row { display: flex; flex-wrap: wrap; gap: 8px; }
.apg-chip { border: 1px solid var(--apg-line); background: transparent; color: var(--apg-ink); padding: 9px 16px; border-radius: 999px; font-size: 0.88rem; cursor: pointer; transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease; }
.apg-chip:hover { border-color: var(--apg-navy); }
.apg-chip--active { background: var(--apg-navy); border-color: var(--apg-navy); color: #fff; }
.apg-field-hint { margin: 0; font-size: 0.82rem; color: var(--apg-ink-soft); }

.apg-checklist { display: flex; flex-direction: column; gap: 8px; }
.apg-check-row { display: flex; align-items: center; justify-content: space-between; padding: 11px 14px; border: 1px solid var(--apg-line); border-radius: var(--apg-r-sm); font-size: 0.88rem; }
.apg-check-row--locked { opacity: 0.55; }
.apg-check-left { display: flex; align-items: center; gap: 10px; }
.apg-check-left svg { width: 17px; height: 17px; }
.apg-check-status { display: flex; align-items: center; gap: 6px; font-weight: 600; }
.apg-check-status svg { width: 15px; height: 15px; }
.apg-check-row--granted .apg-check-status { color: var(--apg-teal); }
.apg-check-row--denied .apg-check-status { color: var(--apg-red); }
.apg-check-row--checking .apg-check-status { color: var(--apg-ink-soft); }

.apg-btn { border: none; border-radius: var(--apg-r-sm); padding: 13px 18px; font-size: 0.92rem; font-weight: 600; cursor: pointer; transition: transform 0.12s ease, box-shadow 0.12s ease, opacity 0.12s ease; }
.apg-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.apg-btn--primary { background: var(--apg-navy); color: #fff; }
.apg-btn--primary:not(:disabled):hover { transform: translateY(-1px); }
.apg-btn--cta { background: var(--apg-gold); color: var(--apg-navy); width: 100%; padding: 15px 18px; font-size: 0.98rem; }
.apg-btn--cta:not(:disabled):hover { transform: translateY(-1px); box-shadow: 0 12px 24px -14px rgba(232,163,61,0.7); }

.apg-error-text { margin: 0; font-size: 0.85rem; color: var(--apg-red); line-height: 1.5; }

.apg-call { min-height: 100vh; background: var(--apg-navy); display: flex; flex-direction: column; }
.apg-call-topbar { display: flex; align-items: center; justify-content: space-between; padding: 20px 28px 8px; }
.apg-domain-pill { display: inline-block; margin-top: 3px; padding: 3px 10px; border-radius: 999px; border: 1px solid rgba(255,255,255,0.18); color: rgba(255,255,255,0.75); font-size: 0.75rem; }
.apg-progress { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; }
.apg-progress-track { width: 160px; height: 6px; border-radius: 999px; background: rgba(255,255,255,0.14); overflow: hidden; }
.apg-progress-fill { height: 100%; background: var(--apg-gold); border-radius: 999px; transition: width 0.4s ease; }
.apg-progress-label { font-size: 0.78rem; color: rgba(255,255,255,0.65); }

.apg-stage { flex: 1; display: grid; grid-template-columns: 1fr 1fr; gap: 18px; padding: 12px 28px; min-height: 0; }
@media (max-width: 820px) { .apg-stage { grid-template-columns: 1fr; } }

.apg-ai-panel { border-radius: var(--apg-r-lg); background: linear-gradient(180deg, var(--apg-navy-soft), var(--apg-navy)); border: 1px solid rgba(255,255,255,0.08); display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px; min-height: 280px; }
.apg-ai-badge { width: 128px; height: 128px; border-radius: 50%; background: var(--apg-navy); border: 2px solid rgba(232,163,61,0.5); color: var(--apg-gold); font-family: 'Space Grotesk', sans-serif; font-size: 2.6rem; font-weight: 700; display: flex; align-items: center; justify-content: center; position: relative; }
.apg-ai-badge::after { content: ''; position: absolute; inset: -10px; border-radius: 50%; border: 2px solid var(--apg-gold); opacity: 0; }
.apg-ai-badge--live::after { animation: apg-tally 1.6s ease-out infinite; }
.apg-ai-caption { margin: 0; color: rgba(255,255,255,0.72); font-size: 0.9rem; }

.apg-candidate-panel { position: relative; border-radius: var(--apg-r-lg); overflow: hidden; background: #000; border: 1px solid rgba(255,255,255,0.08); min-height: 280px; }
.apg-candidate-video { width: 100%; height: 100%; object-fit: cover; }
.apg-nameplate { position: absolute; bottom: 14px; left: 14px; display: flex; align-items: center; gap: 7px; background: rgba(0,0,0,0.55); color: #fff; padding: 5px 12px; border-radius: 999px; font-size: 0.82rem; }
.apg-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--apg-teal); }
.apg-dot--live { box-shadow: 0 0 0 3px rgba(31,138,99,0.25); }

.apg-subtitle-bar { margin: 0 28px 16px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: var(--apg-r-md); padding: 16px 20px; display: flex; gap: 14px; align-items: flex-start; }
.apg-subtitle-avatar { flex-shrink: 0; width: 28px; height: 28px; border-radius: 50%; background: var(--apg-gold); color: var(--apg-navy); font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 0.85rem; display: flex; align-items: center; justify-content: center; }
.apg-subtitle-text { margin: 0; color: #f3f5f8; font-size: 0.98rem; line-height: 1.55; max-width: 72ch; }

.apg-call-error { margin: 0 28px 12px; color: #ffb4ac; font-size: 0.85rem; }

.apg-controls { display: flex; align-items: center; justify-content: center; gap: 18px; padding: 4px 28px 30px; }
.apg-record-btn { width: 60px; height: 60px; border-radius: 50%; border: none; background: var(--apg-gold); color: var(--apg-navy); display: flex; align-items: center; justify-content: center; cursor: pointer; transition: transform 0.12s ease; }
.apg-record-btn svg { width: 24px; height: 24px; }
.apg-record-btn:hover:not(:disabled) { transform: scale(1.05); }
.apg-record-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.apg-record-btn--live { background: var(--apg-red); color: #fff; }
.apg-icon-btn { width: 48px; height: 48px; border-radius: 50%; border: 1px solid rgba(255,255,255,0.25); background: transparent; color: rgba(255,255,255,0.85); display: flex; align-items: center; justify-content: center; cursor: pointer; }
.apg-icon-btn svg { width: 19px; height: 19px; }
.apg-end-btn { display: flex; align-items: center; gap: 8px; border: 1px solid rgba(194,59,59,0.5); background: rgba(194,59,59,0.12); color: #ffb4ac; padding: 0 18px; height: 48px; border-radius: 999px; font-size: 0.88rem; font-weight: 600; cursor: pointer; }
.apg-end-btn svg { width: 17px; height: 17px; }

@keyframes apg-tally { 0% { transform: scale(1); opacity: 0.55; } 100% { transform: scale(1.18); opacity: 0; } }
@keyframes apg-rise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@media (prefers-reduced-motion: reduce) {
  .apg-ai-badge--live::after { animation: none; }
  .apg-lobby-card { animation: none; }
}
`;

export default function App() {
  const [screen, setScreen] = useState<Screen>("landing");
  const [domain, setDomain] = useState<string>(DOMAINS[0].id);

  const [permission, setPermission] = useState<PermissionState>("idle");
  const [permissionError, setPermissionError] = useState<string | null>(null);
  const [micLevel, setMicLevel] = useState<number>(0);

  const [currentQuestion, setCurrentQuestion] = useState<string>("");
  const [questionCount, setQuestionCount] = useState<number>(1);
  const [hiddenDifficulty, setHiddenDifficulty] = useState<string>("Medium");
  const [askedQuestions, setAskedQuestions] = useState<string[]>([]);

  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [status, setStatus] = useState<CallStatus>("ready");
  const [callError, setCallError] = useState<string | null>(null);

  const lobbyVideoRef = useRef<HTMLVideoElement | null>(null);
  const callVideoRef = useRef<HTMLVideoElement | null>(null);
  const localStreamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);

  const audioCtxRef = useRef<AudioContext | null>(null);
  const meterFrameRef = useRef<number | null>(null);

  const canStart = permission === "granted";

  const stopMicMeter = () => {
    if (meterFrameRef.current !== null) cancelAnimationFrame(meterFrameRef.current);
    meterFrameRef.current = null;
    if (audioCtxRef.current) {
      audioCtxRef.current.close().catch(() => {});
      audioCtxRef.current = null;
    }
    setMicLevel(0);
  };

  const startMicMeter = (stream: MediaStream) => {
    try {
      const AudioCtxCtor: typeof AudioContext =
        window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const ctx = new AudioCtxCtor();
      const source = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 512;
      source.connect(analyser);
      audioCtxRef.current = ctx;

      const data = new Uint8Array(analyser.frequencyBinCount);
      const tick = () => {
        analyser.getByteFrequencyData(data);
        let sum = 0;
        for (let i = 0; i < data.length; i++) sum += data[i];
        const avg = sum / data.length;
        setMicLevel(Math.min(1, avg / 90));
        meterFrameRef.current = requestAnimationFrame(tick);
      };
      tick();
    } catch (err) {
      console.error("Mic meter error:", err);
    }
  };

  const attachTrackEndedHandlers = (stream: MediaStream) => {
    stream.getTracks().forEach((track) => {
      track.onended = () => {
        setPermission("denied");
        setPermissionError("Your camera or microphone disconnected. Reconnect them to continue.");
        setScreen("lobby");
        stopMicMeter();
      };
    });
  };

  const requestDevices = async () => {
    setPermission("checking");
    setPermissionError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      localStreamRef.current = stream;
      attachTrackEndedHandlers(stream);
      if (lobbyVideoRef.current) lobbyVideoRef.current.srcObject = stream;
      setPermission("granted");
      startMicMeter(stream);
    } catch (err) {
      console.error("Device access error:", err);
      setPermission("denied");
      setPermissionError(
        err instanceof DOMException && err.name === "NotAllowedError"
          ? "Camera and microphone are blocked. Allow access in your browser's site settings, then try again."
          : "Couldn't reach your camera or microphone. Close any other app using them and try again."
      );
    }
  };

  useEffect(() => {
    return () => {
      stopMicMeter();
      localStreamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  useEffect(() => {
    if (!localStreamRef.current) return;
    const target = screen === "lobby" ? lobbyVideoRef.current : callVideoRef.current;
    if (target) target.srcObject = localStreamRef.current;
  }, [screen]);

  const playAudioSafely = async (audioUrl: string) => {
    const el = audioPlayerRef.current;
    if (!el) {
      setStatus("ready");
      return;
    }

    setStatus("speaking");
    el.src = `${BACKEND_URL}${audioUrl}?t=${Date.now()}`;

    el.onended = () => setStatus("ready");
    el.onpause = () => setStatus("ready");
    el.onerror = () => {
      console.warn("Audio element error; resetting status to ready.");
      setStatus("ready");
    };

    try {
      await el.play();
    } catch (err) {
      console.warn("Autoplay notice/blocked:", err);
      setStatus("ready");
    }
  };

  const handleEnterLobby = (domainId?: string) => {
    if (domainId) setDomain(domainId);
    setScreen("lobby");
  };

  const handleStartInterview = async () => {
    if (!canStart) return;
    stopMicMeter();
    setStatus("analyzing");
    setCallError(null);

    const formData = new FormData();
    formData.append("domain", domain);

    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/start-interview`, { method: "POST", body: formData });
      if (!res.ok) throw new Error(`Server responded ${res.status}`);
      const data = await res.json();

      setCurrentQuestion(data.question_text);
      setAskedQuestions([data.question_text]);
      setQuestionCount(1);
      setHiddenDifficulty("Medium");
      setScreen("interview");

      if (data.audio_url) {
        await playAudioSafely(data.audio_url);
      } else {
        setStatus("ready");
      }
    } catch (err) {
      console.error("Start interview error:", err);
      setStatus("error");
      setCallError("Could not start interview session. Check that the backend server is running.");
    }
  };

  const handleEndInterview = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
    audioPlayerRef.current?.pause();
    setStatus("ready");
    setScreen("lobby");
    setAskedQuestions([]);
    if (localStreamRef.current) startMicMeter(localStreamRef.current);
  };

  const toggleMute = () => {
    if (!localStreamRef.current) return;
    const next = !isMuted;
    localStreamRef.current.getAudioTracks().forEach((t) => (t.enabled = !next));
    setIsMuted(next);
  };

  const startRecording = async () => {
    if (!localStreamRef.current || status === "analyzing" || status === "speaking") return;
    localStreamRef.current.getAudioTracks().forEach((t) => (t.enabled = true));
    setIsMuted(false);
    audioChunksRef.current = [];
    try {
      const audioOnlyStream = new MediaStream(localStreamRef.current.getAudioTracks());
      const mimeType = pickAudioMimeType();
      const mediaRecorder = mimeType ? new MediaRecorder(audioOnlyStream, { mimeType }) : new MediaRecorder(audioOnlyStream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.start();
      setIsRecording(true);
      setStatus("listening");
      setCallError(null);
    } catch (err) {
      console.error("Recording error:", err);
      setStatus("error");
      setCallError("Couldn't start recording. Check your microphone and try again.");
    }
  };

  const stopRecording = () => {
    if (!mediaRecorderRef.current) return;
    mediaRecorderRef.current.onstop = async () => {
      const mimeType = mediaRecorderRef.current?.mimeType || "audio/webm";
      const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
      await submitVoiceTurn(audioBlob);
    };
    mediaRecorderRef.current.stop();
    setIsRecording(false);
    setStatus("analyzing");
  };

  const submitVoiceTurn = async (audioBlob: Blob) => {
    const ext = audioBlob.type.includes("webm")
      ? "webm"
      : audioBlob.type.includes("ogg")
      ? "ogg"
      : audioBlob.type.includes("mp4")
      ? "m4a"
      : "wav";

    const formData = new FormData();
    formData.append("audio_file", audioBlob, `answer.${ext}`);
    formData.append("domain", domain);
    formData.append("current_question", currentQuestion);
    formData.append("current_difficulty", hiddenDifficulty);
    formData.append("question_count", questionCount.toString());
    formData.append("used_questions_json", JSON.stringify(askedQuestions));

    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/voice-turn`, { method: "POST", body: formData });
      if (!res.ok) throw new Error(`Server responded ${res.status}`);
      const data = await res.json();

      setCurrentQuestion(data.question_text);

     

      setAskedQuestions((prev) => {
        if (prev.includes(data.question_text)) return prev;
        return [...prev, data.question_text];
      });

      setHiddenDifficulty(data.hidden_difficulty);
      setQuestionCount(data.question_count);
      setCallError(null);

      if (data.audio_url) {
        await playAudioSafely(data.audio_url);
      } else {
        setStatus("ready");
      }
    } catch (err) {
      console.error("Voice turn error:", err);
      setStatus("error");
      setCallError("Lost connection to the interview server. Check that it's running and try again.");
    }
  };

  const statusLabel = (() => {
    switch (status) {
      case "listening":
        return "Listening\u2026";
      case "analyzing":
        return "Thinking it through\u2026";
      case "speaking":
        return "Aptigrad is speaking\u2026";
      case "error":
        return "Something went wrong";
      default:
        return "Ready when you are";
    }
  })();

  const selectedDomain = DOMAINS.find((d) => d.id === domain);
  const meterBars = [0, 1, 2, 3, 4, 5, 6];

  return (
    <div className="apg-app">
      <style>{GLOBAL_STYLES}</style>

      <audio ref={audioPlayerRef} style={{ display: "none" }} preload="auto" />

      {screen === "landing" && <LandingPage onStart={handleEnterLobby} />}

      {screen === "lobby" && (
        <div className="apg-lobby">
          <div className="apg-lobby-card">
            <div className="apg-lobby-preview">
              {permission === "granted" ? (
                <>
                  <video ref={lobbyVideoRef} autoPlay playsInline muted className="apg-lobby-video" />
                  <div className="apg-meter" aria-hidden="true">
                    {meterBars.map((i) => (
                      <span
                        key={i}
                        className="apg-meter-bar"
                        style={{ transform: `scaleY(${Math.max(0.12, Math.min(1, micLevel * (1.4 - i * 0.12)))})` }}
                      />
                    ))}
                  </div>
                </>
              ) : (
                <div className="apg-preview-empty">
                  <IconCamera />
                  <p>{permission === "checking" ? "Requesting access\u2026" : "Enable your camera to see a preview here."}</p>
                </div>
              )}
            </div>

            <div className="apg-lobby-form">
              <div className="apg-brand">
                <span className="apg-brand-mark">A</span>
                <div>
                  <p className="apg-brand-name">Aptigrad</p>
                  <p className="apg-brand-tag">Mock interview lobby</p>
                </div>
              </div>

              <div>
                <h1 className="apg-lobby-heading">Let&rsquo;s get you set up</h1>
                <p className="apg-lobby-copy">
                  Pick a domain and confirm your camera and microphone. Aptigrad needs both running to start.
                </p>
              </div>

              <div className="apg-field">
                <label className="apg-field-label" id="domain-label">
                  Choose your interview domain
                </label>
                <div className="apg-chip-row" role="radiogroup" aria-labelledby="domain-label">
                  {DOMAINS.map((d) => (
                    <button
                      key={d.id}
                      type="button"
                      role="radio"
                      aria-checked={domain === d.id}
                      className={`apg-chip ${domain === d.id ? "apg-chip--active" : ""}`}
                      onClick={() => setDomain(d.id)}
                    >
                      {d.label}
                    </button>
                  ))}
                </div>
                {selectedDomain && <p className="apg-field-hint">{selectedDomain.blurb}</p>}
              </div>

              <div className="apg-checklist" role="group" aria-label="Device check">
                <div className={`apg-check-row apg-check-row--${permission}`}>
                  <span className="apg-check-left">
                    <IconCamera /> Camera
                  </span>
                  <span className="apg-check-status">
                    {permission === "granted" && (
                      <>
                        <IconCheck /> Ready
                      </>
                    )}
                    {permission === "checking" && "Checking\u2026"}
                    {permission === "denied" && (
                      <>
                        <IconAlert /> Blocked
                      </>
                    )}
                    {permission === "idle" && "Not started"}
                  </span>
                </div>
                <div className={`apg-check-row apg-check-row--${permission}`}>
                  <span className="apg-check-left">
                    <IconMic /> Microphone
                  </span>
                  <span className="apg-check-status">
                    {permission === "granted" && (
                      <>
                        <IconCheck /> Ready
                      </>
                    )}
                    {permission === "checking" && "Checking\u2026"}
                    {permission === "denied" && (
                      <>
                        <IconAlert /> Blocked
                      </>
                    )}
                    {permission === "idle" && "Not started"}
                  </span>
                </div>
                <div className="apg-check-row apg-check-row--locked">
                  <span className="apg-check-left">
                    <IconLock /> Screen share
                  </span>
                  <span className="apg-check-status">Coming soon</span>
                </div>
              </div>

              {permission !== "granted" && (
                <button className="apg-btn apg-btn--primary" onClick={requestDevices} disabled={permission === "checking"}>
                  {permission === "checking" ? "Checking your devices\u2026" : permission === "denied" ? "Try again" : "Enable camera & microphone"}
                </button>
              )}
              {permissionError && <p className="apg-error-text">{permissionError}</p>}

              <button className="apg-btn apg-btn--cta" onClick={handleStartInterview} disabled={!canStart}>
                Start interview
              </button>
            </div>
          </div>
        </div>
      )}

      {screen === "interview" && (
        <div className="apg-call">
          <header className="apg-call-topbar">
            <div className="apg-brand apg-brand--dark">
              <span className="apg-brand-mark apg-brand-mark--sm">A</span>
              <div>
                <p className="apg-brand-name apg-brand-name--sm">Aptigrad</p>
                <span className="apg-domain-pill">{domain}</span>
              </div>
            </div>
            <div className="apg-progress">
              <div className="apg-progress-track">
                <div className="apg-progress-fill" style={{ width: `${Math.min(100, (questionCount / 25) * 100)}%` }} />
              </div>
              <span className="apg-progress-label">Question {questionCount} of 25</span>
            </div>
          </header>

          <div className="apg-stage">
            <div className="apg-ai-panel">
              <div className={`apg-ai-badge ${isRecording || status === "speaking" ? "apg-ai-badge--live" : ""}`}>A</div>
              <p className="apg-ai-caption" aria-live="polite">
                {statusLabel}
              </p>
            </div>
            <div className="apg-candidate-panel">
              <video ref={callVideoRef} autoPlay playsInline muted className="apg-candidate-video" />
              <span className="apg-nameplate">
                <span className="apg-dot apg-dot--live" /> You
              </span>
            </div>
          </div>

          <div className="apg-subtitle-bar">
            <span className="apg-subtitle-avatar">A</span>
            <p className="apg-subtitle-text" aria-live="polite">
              {currentQuestion}
            </p>
          </div>

          {callError && <p className="apg-call-error">{callError}</p>}

          <div className="apg-controls">
            <button
              className={`apg-record-btn ${isRecording ? "apg-record-btn--live" : ""}`}
              onClick={isRecording ? stopRecording : startRecording}
              disabled={status === "analyzing" || status === "speaking"}
              aria-label={isRecording ? "Stop recording your answer" : "Record your answer"}
            >
              {isRecording ? <IconStop /> : <IconMic />}
            </button>
            <button className="apg-icon-btn" onClick={toggleMute} aria-label={isMuted ? "Unmute microphone" : "Mute microphone"}>
              {isMuted ? <IconSpeakerMute /> : <IconSpeaker />}
            </button>
            <button className="apg-end-btn" onClick={handleEndInterview}>
              <IconEndCall /> End interview
            </button>
          </div>
        </div>
      )}
    </div>
  );
}