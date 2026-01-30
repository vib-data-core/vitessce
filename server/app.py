import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

BASE_DIR = Path(os.environ.get("VITESSCE_BASE_DIR", "/data/groups")).resolve()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def resolve_under_base(path_str: str) -> Path:
    raw_path = Path(path_str)
    if raw_path.is_absolute():
        abs_path = raw_path.resolve()
    else:
        abs_path = (BASE_DIR / raw_path).resolve()

    try:
        abs_path.relative_to(BASE_DIR)
    except ValueError:
        raise HTTPException(status_code=403, detail="Path outside base directory")

    return abs_path


@app.get("/api/config")
def get_config(path: str):
    abs_path = resolve_under_base(path)
    if not abs_path.is_file():
        raise HTTPException(status_code=404, detail="Config not found")

    try:
        with abs_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Config is not valid JSON")

    return JSONResponse(content=data)


@app.get("/data/{path:path}")
def get_data(path: str):
    abs_path = resolve_under_base(path)
    if not abs_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(abs_path)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
