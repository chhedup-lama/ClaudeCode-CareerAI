import asyncio
import io
import json
import queue
import threading
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from agents.orchestrator import run_streaming

app = FastAPI(title="CareerAI — Workforce Intelligence")

DATA_DIR = Path(__file__).parent / "data"
STATIC_DIR = Path(__file__).parent / "static"
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
REQUIRED_UPLOAD_COLUMNS = {"job_family", "region", "salary", "year"}


@app.get("/", response_class=HTMLResponse)
async def index():
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        return JSONResponse(
            {"error": "Invalid file type. Upload a .csv or .xlsx file."},
            status_code=400,
        )

    content = await file.read()
    try:
        df = (
            pd.read_excel(io.BytesIO(content))
            if suffix in {".xlsx", ".xls"}
            else pd.read_csv(io.BytesIO(content))
        )
    except Exception as e:
        return JSONResponse({"error": f"Could not read file: {e}"}, status_code=400)

    df.columns = df.columns.str.lower()
    missing_cols = REQUIRED_UPLOAD_COLUMNS - set(df.columns)
    if missing_cols:
        return JSONResponse(
            {
                "error": (
                    f"Missing required columns: {sorted(missing_cols)}. "
                    f"Required: job_family, region, salary, year. Optional: level"
                )
            },
            status_code=400,
        )

    df.to_csv(DATA_DIR / "salary_data.csv", index=False)
    return JSONResponse(
        {
            "message": f"Salary data uploaded successfully. {len(df):,} rows loaded.",
            "rows": len(df),
            "columns": list(df.columns),
        }
    )


@app.get("/stream")
async def stream(q: str):
    if not q.strip():
        return JSONResponse({"error": "No query provided."}, status_code=400)

    event_queue: queue.Queue = queue.Queue()

    def emit(event_type: str, data: dict) -> None:
        event_queue.put({"type": event_type, "data": data})

    def run_pipeline() -> None:
        try:
            run_streaming(q, emit)
        except Exception as e:
            event_queue.put({"type": "error", "data": {"message": str(e)}})
        finally:
            event_queue.put(None)  # sentinel

    thread = threading.Thread(target=run_pipeline, daemon=True)
    thread.start()

    async def generate():
        loop = asyncio.get_event_loop()
        while True:
            event = await loop.run_in_executor(None, event_queue.get)
            if event is None:
                yield 'data: {"type": "done"}\n\n'
                break
            yield f"data: {json.dumps(event, default=str)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
