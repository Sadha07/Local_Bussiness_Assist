# Frontend (React + HTTP API)

## Backend (from project root)

```bash
uvicorn backend.api_server:app --host 0.0.0.0 --port 8000 --reload
```

## 1) Install

```bash
npm install
```

## 2) Configure backend API URL

Copy `.env.example` to `.env` and update value if needed:

```env
VITE_API_URL=http://localhost:8000
```

## 3) Run

```bash
npm run dev
```

Open the URL shown by Vite (typically `http://localhost:5173`).
