"""FastAPI entry point for the local ArtMockery application."""
import json
from pathlib import Path
import traceback
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from mockup.renderer import render_mockup

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="ArtMockery", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/")
def index():
    return FileResponse(BASE_DIR / "static" / "index.html", media_type="text/html")


@app.get("/health")
def health():
    return {"status": "ok", "app": "ArtMockery"}


@app.post("/api/render")
async def render_api(
    painting: UploadFile = File(...),
    settings: str = Form(...),
    wall_photo: Optional[UploadFile] = File(None),
):
    try:
        options = json.loads(settings)
        painting_bytes = await painting.read()
        wall_bytes = await wall_photo.read() if wall_photo else None
        if len(painting_bytes) > 30 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Painting image must be under 30 MB.")
        if wall_bytes and len(wall_bytes) > 30 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Wall photo must be under 30 MB.")
        data, media_type = render_mockup(painting_bytes, options, wall_bytes)
        extension = "jpg" if media_type == "image/jpeg" else "png"
        return Response(
            content=data,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="artmockery.{extension}"'},
        )
    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(exc))
