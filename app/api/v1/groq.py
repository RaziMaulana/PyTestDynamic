from __future__ import annotations
from datetime import date
import os

from fastapi import APIRouter, HTTPException
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.components import WorkspaceResponse, GenerateRequest
from app.security import mask_sensitive_data

router = APIRouter(prefix="/workspace", tags=["workspace"])

api_key = settings.groq_api_key or os.getenv("GROQ_API_KEY", "")
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0.2, max_tokens=2500, api_key=api_key)
structured_pipeline = llm.with_structured_output(WorkspaceResponse)

SYSTEM_PROMPT_TEMPLATE = """Kamu adalah UI Engine spesialis KESEHATAN FISIK dan BIOMEKANIK.

Hari ini tanggal {today}.

TUGAS UTAMA:
1. Evaluasi prompt: Apakah ini tentang kesehatan fisik, postur, cedera, fisioterapi, atau biomekanik?
2. JIKA YA: Set is_clinical_query = True. Buatkan analisis klinis dengan metrik dan chart yang relevan (Wajib isi `props.data` untuk chart).
3. JIKA TIDAK (misal: memasak, backflip candaan, coding, tugas harian): Set is_clinical_query = False. DILARANG KERAS membuat analogi kebugaran untuk topik di luar konteks.

Jawab dalam Bahasa Indonesia dan patuhi struktur JSON WorkspaceResponse."""

@router.post("/generate", response_model=WorkspaceResponse)
async def generate_workspace_with_groq(payload: GenerateRequest):
    if not payload.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt tidak boleh kosong.")

    try:
        # PII Masking
        safe_prompt = mask_sensitive_data(payload.prompt)
        
        # Guardrail Tersembunyi
        guardrail = "\n\n(SISTEM: Jika prompt BUKAN evaluasi kesehatan serius, pastikan is_clinical_query = False. Jangan gunakan analogi.)"
        user_input = safe_prompt + guardrail
        
        if payload.previousContext:
            user_input = f"Konteks sebelumnya: {payload.previousContext}\nModifikasi: {safe_prompt}{guardrail}"

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(today=date.today().isoformat())
        result = await structured_pipeline.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_input)
        ])

        # OVERRIDE MUTLAK
        if getattr(result, "is_clinical_query", True) is False:
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
                            "notesContent": "Mohon berikan prompt yang berkaitan dengan kesehatan atau postur tubuh."
                        }
                    }
                ],
                "refinement": {
                    "question": "Ingin mencoba analisis yang sesuai?",
                    "options": ["Analisis postur duduk", "Evaluasi nyeri sendi"]
                }
            }

        return result

    except Exception as e:
        return {
            "is_clinical_query": True,
            "workspaceTitle": "Sedang Memuat...",
            "description": "Gagal merender format.",
            "widgets": [],
            "refinement": {"question": "Ulangi pertanyaan?", 
                           "options": ["Coba Lagi", "Ganti Topik"]}
        }