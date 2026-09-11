import React, { useState, useRef } from "react";

interface AIResponse {
  user_transcription: string;
  score: number;
  feedback: string;
  next_question: string;
  new_difficulty: string;
  audio_url: string;
}

const BACKEND_BASE_URL = "http://127.0.0.1:8000";

export default function App() {
  // Domain & State Management
  const [domain, setDomain] = useState<string>("Software Engineering");
  const [currentDifficulty, setCurrentDifficulty] = useState<string>("Medium");
  const [currentQuestion, setCurrentQuestion] = useState<string>(
    "Explain the difference between process and thread in OS."
  );

  // Recording State & Results
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [status, setStatus] = useState<string>("Ready to begin session");
  const [evaluation, setEvaluation] = useState<AIResponse | null>(null);

  // Refs for Media Recording & Audio Playback
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);

  // Start Microphone Recording
  const startRecording = async () => {
    audioChunksRef.current = [];
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event: BlobEvent) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
      setStatus("Listening to your voice response...");
    } catch (err) {
      console.error("Microphone Access Error:", err);
      setStatus("Error accessing microphone. Check browser permissions.");
    }
  };

  // Stop Microphone Recording & Send to FastAPI
  const stopRecording = () => {
    if (!mediaRecorderRef.current) return;

    mediaRecorderRef.current.stop();
    setIsRecording(false);
    setStatus("Transcribing audio and processing AI response...");

    mediaRecorderRef.current.onstop = async () => {
      const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
      await sendAudioToBackend(audioBlob);
    };
  };

  // POST Audio Chunk to FastAPI Voice Endpoint
  const sendAudioToBackend = async (audioBlob: Blob) => {
    const formData = new FormData();
    formData.append("audio_file", audioBlob, "user_response.wav");
    formData.append("domain", domain);
    formData.append("current_question", currentQuestion);
    formData.append("current_difficulty", currentDifficulty);

    try {
      const response = await fetch(`${BACKEND_BASE_URL}/api/v1/voice-turn`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server returned error status ${response.status}`);
      }

      const data: AIResponse = await response.json();

      // Update Session State with Response
      setEvaluation(data);
      setCurrentDifficulty(data.new_difficulty);
      setCurrentQuestion(data.next_question);
      setStatus("AI Interviewer finished evaluation.");

      // Play Generated Voice Audio Stream
      if (audioPlayerRef.current) {
        audioPlayerRef.current.src = `${BACKEND_BASE_URL}${data.audio_url}`;
        audioPlayerRef.current.play();
      }
    } catch (err) {
      console.error("API Call Error:", err);
      setStatus("Failed to communicate with AptiGrad backend.");
    }
  };

  return (
    <div style={{ maxWidth: "800px", margin: "40px auto", fontFamily: "sans-serif", padding: "0 20px" }}>
      <h1>AptiGrad AI Voice Interview Test Bench</h1>

      {/* Onboarding Domain Selection */}
      <div style={{ background: "#f5f5f5", padding: "16px", borderRadius: "8px", marginBottom: "20px" }}>
        <h3>Domain Settings</h3>
        <label>
          Domain:{" "}
          <input
            type="text"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            style={{ padding: "6px 10px", fontSize: "1rem" }}
          />
        </label>
        <span style={{ marginLeft: "20px", fontWeight: "bold" }}>
          Level: <span style={{ color: "#d35400" }}>{currentDifficulty}</span>
        </span>
      </div>

      {/* Dynamic Question Container */}
      <div style={{ background: "#eef2f5", padding: "20px", borderRadius: "8px", marginBottom: "20px" }}>
        <h3 style={{ margin: 0, color: "#333" }}>Active Question:</h3>
        <p style={{ fontSize: "1.2rem", fontWeight: "500", marginTop: "10px", color: "#1a252f" }}>
          {currentQuestion}
        </p>
      </div>

      {/* Controls */}
      <div style={{ background: "#fff", border: "1px solid #ddd", padding: "20px", borderRadius: "8px", marginBottom: "20px" }}>
        <h3>Voice Controls</h3>
        <button
          onClick={startRecording}
          disabled={isRecording}
          style={{
            padding: "10px 20px",
            fontSize: "1rem",
            backgroundColor: "#e74c3c",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: isRecording ? "not-allowed" : "pointer",
            marginRight: "10px",
          }}
        >
          🎤 Start Speaking
        </button>

        <button
          onClick={stopRecording}
          disabled={!isRecording}
          style={{
            padding: "10px 20px",
            fontSize: "1rem",
            backgroundColor: "#2ecc71",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: !isRecording ? "not-allowed" : "pointer",
          }}
        >
          ⏹️ Stop & Submit
        </button>

        <p style={{ marginTop: "15px", fontStyle: "italic", color: "#666" }}>
          Status: <strong>{status}</strong>
        </p>
      </div>

      {/* AI Feedback & Scorecard Component */}
      {evaluation && (
        <div style={{ background: "#e8f8f5", padding: "20px", borderRadius: "8px", border: "1px solid #a3e4d7" }}>
          <h3>AI Live Feedback</h3>
          <p><strong>Your Response Transcribed:</strong> "{evaluation.user_transcription}"</p>
          <p><strong>Score:</strong> <span style={{ fontSize: "1.2rem", fontWeight: "bold" }}>{evaluation.score}/10</span></p>
          <p><strong>Feedback:</strong> {evaluation.feedback}</p>
          
          <h4 style={{ marginTop: "15px" }}>AI Voice Audio Output:</h4>
          <audio ref={audioPlayerRef} controls style={{ width: "100%" }} />
        </div>
      )}
    </div>
  );
}