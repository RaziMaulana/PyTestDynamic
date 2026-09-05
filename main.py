from __future__ import annotations

from contextlib import asynccontextmanager
from dotenv import load_dotenv

# 1. Load environment variables paling awal sebelum modul lain dipanggil
load_dotenv()

from app.config import settings
from app.api.v1 import groq

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup tambahan saat startup/shutdown aplikasi bisa diletakkan di sini
    yield

# 2. Inisialisasi instance FastAPI tunggal
app = FastAPI(title=settings.app_name, lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

# ==========================================
# 3. Pendaftaran Router API v1
# ==========================================
# Seluruh logika AI, Pydantic, Presidio masking, dan deteksi is_clinical_query
# sekarang berjalan dan terisolasi dengan rapi di dalam app/api/v1/groq.py
app.include_router(groq.router, prefix=settings.api_v1_prefix)


# ==========================================
# 4. Endpoints Dasar & Frontend
# ==========================================
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "message": "Clinical Biomechanics Engine is running."}

@app.get("/", response_class=HTMLResponse)
async def serve_home(request: Request):
    # Merender file templates/index.html
    return templates.TemplateResponse(request=request, name="index.html")

# Mount direktori frontend statis jika disetel di config
if settings.web_dist_dir.is_dir():
    app.mount(
        "/", StaticFiles(directory=settings.web_dist_dir, html=True), name="web"
    )

if __name__ == "__main__":
    import uvicorn
    # Menjalankan server uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=getattr(settings, "port", 8000), reload=True)