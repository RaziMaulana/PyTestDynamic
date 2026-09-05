import os
from typing import List, Optional, Literal
from dotenv import load_dotenv

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

app = FastAPI(title="Full-Stack FastAPI Dynamic Workspace")
templates = Jinja2Templates(directory="templates")

# ==========================================
# 1. Pydantic Models (Skema Structured Output)
# ==========================================

class ChartDataPoint(BaseModel):
    label: str = Field(description="Label metrik atau titik waktu")
    value: float = Field(description="Nilai numerik metrik")

class BodyPoint(BaseModel):
    part: Literal[
        "brain", "chest", "heart", "abdomen", 
        "arms", "shoulders", "hips", "legs", "knees", "ankles", "back"
    ] = Field(description="Bagian tubuh yang difokuskan")
    status: Literal["normal", "warning", "active"] = Field(description="Kondisi visual titik")
    description: str = Field(description="Catatan kondisi spesifik organ/sendi")

class WidgetProps(BaseModel):
    data: Optional[List[ChartDataPoint]] = Field(default=None)
    metricValue: Optional[str] = Field(default=None)
    unit: Optional[str] = Field(default=None)
    bodyPoints: Optional[List[BodyPoint]] = Field(default=None)

class WidgetItem(BaseModel):
    id: str = Field(description="ID unik widget, misal: 'w_1'")
    type: Literal[
        "TaskTracker", "MarkdownNotes", "MetricCard", 
        "BarChart", "LineChart", "DonutChart", "BodyAnatomyMap"
    ] = Field(description="Jenis komponen tampilan")
    title: str = Field(description="Judul widget")
    colSpan: int = Field(ge=3, le=12, description="Lebar kolom grid (minimal 6 jika BodyAnatomyMap)")
    props: Optional[WidgetProps] = Field(default=None)

class RefinementHook(BaseModel):
    question: str = Field(description="Satu pertanyaan cerdas untuk evaluasi susunan layout")
    options: List[str] = Field(min_length=2, max_length=3, description="2-3 pilihan saran cepat")

class WorkspaceResponse(BaseModel):
    workspaceTitle: str = Field(description="Judul representatif ruang kerja")
    description: Optional[str] = Field(default=None, description="Ringkasan susunan widget")
    widgets: List[WidgetItem] = Field(description="Daftar widget yang disusun")
    refinement: Optional[RefinementHook] = Field(default=None)

class GenerateRequest(BaseModel):
    prompt: str
    previousContext: Optional[str] = None

# ==========================================
# 2. LangChain Pipeline Setup
# ==========================================

api_key = os.getenv("GROQ_API_KEY", "")

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.2,
    max_tokens=2500,
    api_key=api_key
)

structured_pipeline = llm.with_structured_output(WorkspaceResponse)

SYSTEM_PROMPT = """Anda adalah Clinical & Physical Biomechanics UI Engine.
Tugas:
1. Ruang lingkup Anda TERBATAS HANYA pada pemantauan kesehatan fisik, rehabilitasi, fisioterapi, beban biomekanik atlet/pekerja, dan keluhan organ tubuh. Tolak secara halus konteks di luar kesehatan dengan tetap memetakannya ke analogi fisik/kebugaran.
2. Setiap rancangan ruang kerja WAJIB menyertakan 'BodyAnatomyMap' (colSpan 6 atau 12) dengan 2-4 titik organ/sendi ('bodyPoints') yang relevan beserta status visualnya ('normal', 'warning', 'active').
3. Lengkapi dengan komponen pendukung klinis:
   - MetricCard: denyut nadi/BPM, VO2Max, tekanan darah, skala nyeri (VAS), kalori terbakar.
   - LineChart / BarChart: tren pemulihan sendi, durasi terapi mingguan, tingkat mobilitas.
   - TaskTracker: protokol pemulihan/rehabilitasi, checklist hidrasi/obat.
4. Buat pertanyaan 'refinement' yang spesifik seputar tindak lanjut klinis atau penyesuaian terapi fisik."""

structured_pipeline = llm.with_structured_output(WorkspaceResponse)
# ==========================================
# 3. Router & Endpoints
# ==========================================

@app.get("/", response_class=HTMLResponse)
async def serve_home(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="index.html"
    )

@app.post("/api/generate-workspace", response_model=WorkspaceResponse)
async def generate_workspace(payload: GenerateRequest):
    if not payload.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt tidak boleh kosong.")

    try:
        user_input = payload.prompt
        if payload.previousContext:
            user_input = f"Konteks ruang kerja sebelumnya: {payload.previousContext}\nInstruksi perbaikan: {payload.prompt}"

        result = await structured_pipeline.ainvoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_input)
        ])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)