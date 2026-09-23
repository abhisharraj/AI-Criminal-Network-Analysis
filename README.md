# AI-Powered Criminal Network Analysis System

## Start the application

The `venv` folder in the original archive was created with `C:\Python313`, which is not portable and is unavailable on this machine. Create a fresh environment from the project root:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the URL shown by Vite (normally `http://localhost:5173`). The API is available at `http://127.0.0.1:8000`.

## Data contract

Communication relationships use a numeric `count` field throughout the backend and frontend. The graph builder, pattern detector, correlation engine, and evidence tracker still accept the previous `call_count` field so old saved records remain usable.
