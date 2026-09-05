from __future__ import annotations
from datetime import date
import os
from fastapi import APIRouter, HTTPException
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import settings

from app.schemas import GenerateRequest, WorkspaceResponse

router = APIRouter(prefix="/workspace", tags=["workspace"])

# Inisialisasi Groq API key dari environment
api_key = getattr(settings, "groq_api_key", None) or os.getenv("GROQ_API_KEY", "")

if not api_key:
    raise ValueError("GROQ_API_KEY belum terdeteksi. Pastikan sudah diatur di file .env")

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.2,
    max_tokens=2500,
    api_key=api_key
)

structured_pipeline = llm.with_structured_output(WorkspaceResponse)

SYSTEM_PROMPT_TEMPLATE = """Kamu adalah Clinical & Physical Biomechanics UI Engine yang ditenagai oleh Groq LLM, asisten spesialis pemantauan kesehatan fisik, rehabilitasi, fisioterapi, dan beban biomekanik tubuh.

Hari ini tanggal {today}.

ATURAN UTAMA & LINGKUP:
- Ruang lingkupmu HANYA seputar kesehatan fisik, analisis postur, pemulihan sendi/otot, dan kebugaran tubuh.
- PENTING (PENANGANAN DI LUAR KONTEKS): Jika user memasukkan prompt di luar kesehatan (misal: kinerja server, penjualan bisnis, coding, dll.), JANGAN MENOLAK secara mentah atau melempar error. Alihkan topik tersebut secara kreatif menjadi analogi kebugaran fisik atau biomekanik tubuh.
- JANGAN PERNAH merespons dengan teks percakapan biasa. Setiap respons HARUS menghasilkan struktur layout WorkspaceResponse yang lengkap.
- Setiap layout WAJIB memuat 'BodyAnatomyMap' (colSpan 6 atau 12) dengan titik tubuh relevan beserta status visualnya ('normal', 'warning', 'active').
- Jawab dalam Bahasa Indonesia."""

@router.post("/generate", response_model=WorkspaceResponse)
async def generate_workspace_with_groq(payload: GenerateRequest):
    if not payload.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt tidak boleh kosong.")

    try:
        user_input = payload.prompt
        if payload.previousContext:
            user_input = f"Konteks ruang kerja sebelumnya: {payload.previousContext}\nInstruksi modifikasi: {payload.prompt}"

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(today=date.today().isoformat())

        # Eksekusi pipeline terstruktur via Groq
        result = await structured_pipeline.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_input)
        ])
        return result

    except Exception as e:
        # Fallback aman jika terjadi gangguan koneksi/parsing pada Groq API
        return {
            "workspaceTitle": "Evaluasi & Pemulihan Biomekanik Umum",
            "description": "Sistem memetakan parameter input ke dalam pemantauan ketahanan fisik dan ergonomi tubuh secara umum.",
            "widgets": [
                {
                    "id": "fallback_w1",
                    "type": "BodyAnatomyMap",
                    "title": "Pemindaian Postur & Ketegangan Otot",
                    "colSpan": 6,
                    "props": {
                        "bodyPoints": [
                            {"part": "back", "status": "warning", "description": "Perhatikan area punggung/lumbar."},
                            {"part": "neck", "status": "normal", "description": "Kondisi otot leher dalam stabil."}
                        ]
                    }
                },
                {
                    "id": "fallback_w2",
                    "type": "MetricCard",
                    "title": "Indeks Stabilitas Fisik",
                    "colSpan": 6,
                    "props": {
                        "metricValue": "85",
                        "unit": "Score"
                    }
                }
            ],
            "refinement": {
                "question": "Apakah Anda ingin memfokuskan analisis ini pada area otot atau sendi tertentu?",
                "options": ["Fokus pada nyeri punggung", "Evaluasi kelelahan lengan/pergelangan", "Kembali ke parameter awal"]
            }
        }