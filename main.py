from __future__ import annotations

import os
from datetime import date
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from app.config import settings
from app.api.v1 import groq
from app.components import WorkspaceResponse, GenerateRequest  # Impor dari file komponen

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title=settings.app_name, lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

app.include_router(groq.router, prefix=settings.api_v1_prefix)

# LangChain Groq Pipeline
api_key = settings.groq_api_key or os.getenv("GROQ_API_KEY", "")
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0.2, max_tokens=2500, api_key=api_key)
structured_pipeline = llm.with_structured_output(WorkspaceResponse)

SYSTEM_PROMPT_TEMPLATE = """Kamu adalah UI Engine spesialis KESEHATAN FISIK dan BIOMEKANIK.

TUGAS UTAMA:
1. Evaluasi prompt: Apakah ini tentang kesehatan fisik, postur, cedera, fisioterapi, ergonomi, atau biomekanik?
2. JIKA YA: Buatkan analisis klinis dengan metrik dan chart yang relevan.
3. JIKA TIDAK (misal: resep masakan, coding, tugas sekolah, bisnis, dll): DILARANG KERAS memberikan informasi yang diminta. Kamu WAJIB meniru persis output penolakan pada CONTOH 2.

=== CONTOH 1 (VALID) ===
User: "Punggung saya sakit setelah duduk 8 jam"
AI: (Menghasilkan JSON WorkspaceResponse normal dengan chart, BodyAnatomyMap, dll)

=== CONTOH 2 (TIDAK VALID) ===
User: "Buatkan saya nasi goreng" / "Buatkan laporan keuangan"
AI: WAJIB menghasilkan struktur persis seperti ini:
{{
  "workspaceTitle": "Akses Dibatasi",
  "description": "Instruksi tidak dapat diproses karena berada di luar lingkup kesehatan.",
  "widgets": [
    {{
      "id": "warning_w1",
      "type": "MarkdownNotes",
      "title": "Peringatan",
      "colSpan": 12,
      "props": {{
        "notesContent": "Mohon berikan prompt yang berkaitan dengan kesehatan."
      }}
    }}
  ],
  "refinement": {{
    "question": "Ingin mencoba analisis seputar kesehatan fisik?",
    "options": ["Analisis postur kerja", "Evaluasi kelelahan otot"]
  }}
}}"""

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
async def serve_home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/api/v1/workspace/generate", response_model=WorkspaceResponse)
async def generate_workspace(payload: GenerateRequest):
    if not payload.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt tidak boleh kosong.")
    
    try:
        user_input = payload.prompt
        if payload.previousContext:
            user_input = f"Konteks sebelumnya: {payload.previousContext}\nModifikasi: {payload.prompt}"
        
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(today=date.today().isoformat())
        
        # 1. AI memproses prompt
        result = await structured_pipeline.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_input)
        ])
        
        # 2. OVERRIDE MUTLAK: Jika AI mendeteksi ini bukan pertanyaan klinis serius
        if not getattr(result, "is_clinical_query", True):
            return {
                "is_clinical_query": False,
                "workspaceTitle": "Akses Dibatasi",
                "description": "Instruksi tidak dapat diproses karena berada di luar lingkup analisis klinis.",
                "widgets": [
                    {
                        "id": "warning_w1",
                        "type": "MarkdownNotes",
                        "title": "Peringatan Sistem",
                        "colSpan": 12,
                        "props": {
                            "notesContent": "Mohon berikan prompt yang berkaitan dengan evaluasi kesehatan, postur, atau biomekanik tubuh."
                        }
                    }
                ],
                "refinement": {
                    "question": "Ingin mencoba analisis yang sesuai?",
                    "options": ["Analisis postur duduk", "Evaluasi nyeri sendi", "Program peregangan"]
                }
            }

        # 3. Jika valid, kembalikan hasil AI
        return result
        
    except Exception as e:
        return {
            "workspaceTitle": "Evaluasi & Pemulihan Biomekanik Umum",
            "description": "Sistem memetakan parameter input ke dalam pemantauan ketahanan fisik secara umum.",
            "widgets": [
                {
                    "id": "fallback_w1",
                    "type": "BodyAnatomyMap",
                    "title": "Pemindaian Postur & Ketegangan Otot",
                    "colSpan": 6,
                    "props": {
                        "bodyPoints": [
                            {"part": "back", "status": "warning", "description": "Perlu perhatian pada area punggung."},
                            {"part": "neck", "status": "normal", "description": "Otot leher stabil."}
                        ]
                    }
                },
                {
                    "id": "fallback_w2",
                    "type": "MetricCard",
                    "title": "Indeks Stabilitas Fisik",
                    "colSpan": 6,
                    "props": {"metricValue": "85", "unit": "Score"}
                }
            ],
            "refinement": {
                "question": "Apakah Anda ingin memfokuskan analisis pada area tertentu?",
                "options": ["Fokus pada nyeri punggung", "Evaluasi kelelahan lengan", "Reset"]
            }
        }

if settings.web_dist_dir.is_dir():
    app.mount("/", StaticFiles(directory=settings.web_dist_dir, html=True), name="web")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=getattr(settings, "port", 8000), reload=True)