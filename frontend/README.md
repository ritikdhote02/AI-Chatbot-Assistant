# Chat Point — Frontend

A high-performance, elegant React.js + Vite web application for the **AI Knowledge Assistant**, providing continuous conversational workflows and full management of long-term & episodic memories.

## Highlights & Features

- **Seamless Authentication**: Registration, email verification handling (`/verify-email?token=...`), resend verification flow, and JWT-authenticated session persistence.
- **Rich Conversational Interface**:
  - Live message streaming & markdown rendering with syntax-highlighted code blocks, copy-to-clipboard, tables, and lists.
  - Context indicators and smart auto-scroll with manual jump-to-bottom control.
  - Prompt starter cards for quick access to core capabilities.
- **Immediate Memory Extraction**: One-click structured memory extraction (`POST /conversations/{id}/extract-memories`) to identify facts, preferences, goals, decisions, and corrections.
- **Episodic Memory Summaries**: Automatic summarization into ChromaDB episodic vectors (`POST /conversations/{id}/episode`) and exploration view (`/episodes`).
- **Long-Term Memory Vault**: Filter by category (`fact`, `preference`, `goal`, `decision`, `correction`), search, create, update, and delete memories with instant feedback (`/memories`).
- **Cognitive Architecture Inspector**: Modal diagram explaining the 3-tier dynamic context assembly (SQLite history + ChromaDB episodic memory + ChromaDB long-term memory) and the 5-message background extraction loop.
- **Zero-CORS Vite Proxy**: Automatically forwards `/auth`, `/conversations`, `/memories`, and `/episodes` to the FastAPI backend (`http://127.0.0.1:8000`) in development without altering any backend code.
- **Zero Vulnerabilities**: Audited with `npm audit` (0 vulnerabilities).

## Technology Stack

- **Framework**: React 18 + Vite 6
- **Routing**: React Router 7
- **Styling**: Tailwind CSS v4 + Plus Jakarta Sans & JetBrains Mono typography
- **Icons**: Lucide React
- **Markdown**: React-Markdown + Remark-GFM
- **State & Alerts**: Context API (`AuthContext`, `ToastContext`) + Animated Notification Toasts

## Getting Started

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Run the Development Server

```bash
npm run dev
```

The frontend will run at `http://localhost:5173`. Make sure the FastAPI backend is running on `http://127.0.0.1:8000`.

### 3. Build for Production

```bash
npm run build
```

Production artifacts will be generated in `frontend/dist/`.
