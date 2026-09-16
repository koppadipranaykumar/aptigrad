# 🎓 AptiGrad — AI-Powered Mock Technical Interviewer

AptiGrad is an adaptive, full-stack AI technical interview platform designed to conduct interactive mock interviews across various core computer science domains. It evaluates candidate answers in real time, adjusts technical difficulty dynamically, generates automated voice turns, and outputs detailed candidate scorecards.

🌐 **Live Demo:** [https://aptigrad.vercel.app](https://aptigrad.vercel.app)

---

## ✨ Features

- 🎙️ **Interactive Voice & Text Interview Loops:** Evaluates spoken audio responses via Whisper Speech-to-Text and generates natural spoken audio using Edge-TTS.
- ⚡ **24/7 Cloud Architecture:** Powered by FastAPI on Render and connected to Groq's high-speed LPU cloud API (`llama-3.2-3b-preview`) for zero-cost, 24/7 global availability.
- 🎯 **Domain-Specific Boundaries:** Strictly tailors technical questions across Data Structures & Algorithms, Java, Python, C, C++, JavaScript, DBMS, Computer Networks, and Operating Systems.
- 📊 **Adaptive Difficulty Engine:** Tracks user performance turn-by-turn to dynamically adjust question difficulty (`INCREASE`, `DECREASE`, `MAINTAIN`).
- 📈 **Automated Performance Scorecard:** Summarizes average performance scores, detailed feedback lists, and final candidate ratings upon completion.

---

## 🛠️ Tech Stack & Architecture

### **Frontend**
- **Framework:** React + TypeScript (Vite)
- **Deployment:** Vercel

### **Backend**
- **Framework:** FastAPI (Python 3.10+) + Uvicorn
- **AI Inference Engine:** Groq API (`llama-3.2-3b-preview`)
- **Speech-to-Text (STT):** `faster-whisper`
- **Text-to-Speech (TTS):** `edge-tts`
- **Deployment:** Render (Free Web Service)

---

## 📂 Project Structure

```text
aptigrad/
├── backend/
│   ├── main.py              # FastAPI application logic & API endpoints
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/                 # React components & UI interfaces
│   └── package.json         # Node dependencies & scripts
├── DockerFile               # Container configuration for GPU/CPU deployments
└── README.md                # Project documentation
