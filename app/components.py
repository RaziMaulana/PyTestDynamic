from __future__ import annotations

from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class ChartDataPoint(BaseModel):
    label: str = Field(description="Label kategori, waktu, atau fase")
    value: float = Field(description="Nilai numerik untuk data chart")

class BodyPoint(BaseModel):
    part: str = Field(description="Bagian tubuh (misal: neck, back, wrists, knees, shoulders)")
    status: Literal["normal", "warning", "active"] = Field(description="Status visual titik")
    description: str = Field(description="Catatan klinis bagian tubuh tersebut")

class WidgetProps(BaseModel):
    data: Optional[List[ChartDataPoint]] = Field(default=None, description="Data deret waktu atau kategori untuk Line/Bar/Donut chart")
    metricValue: Optional[str] = Field(default=None, description="Nilai utama untuk MetricCard")
    unit: Optional[str] = Field(default=None, description="Satuan ukuran")
    bodyPoints: Optional[List[BodyPoint]] = Field(default=None, description="Titik pemetaan anatomi tubuh")
    notesContent: Optional[str] = Field(default=None, description="Konten teks markdown untuk catatan medis")
    tasks: Optional[List[str]] = Field(default=None, description="Daftar tugas rehabilitasi atau fisioterapi")

class WidgetItem(BaseModel):
    id: str = Field(description="ID unik widget, misal: w_1")
    type: Literal[
        "TaskTracker", "MarkdownNotes", "MetricCard", 
        "BarChart", "LineChart", "DonutChart", "BodyAnatomyMap"
    ] = Field(description="Pilih tipe chart/widget yang paling relevan dengan analisis fisik")
    title: str = Field(description="Judul widget")
    colSpan: int = Field(ge=3, le=12, description="Ukuran lebar grid 12 kolom (misal: 6 untuk separuh layar, 12 untuk penuh)")
    props: Optional[WidgetProps] = Field(default=None)

class RefinementHook(BaseModel):
    question: str = Field(description="Pertanyaan lanjutan untuk eksplorasi kesehatan")
    options: List[str] = Field(min_length=2, max_length=3, description="2-3 pilihan cepat")

class WorkspaceResponse(BaseModel):
    is_clinical_query: bool = Field(description="WAJIB True jika prompt meminta evaluasi medis/ergonomi serius. WAJIB False jika candaan (seperti 'backflip dong'), resep masakan, tugas sekolah, atau coding.")
    workspaceTitle: str = Field(description="Judul evaluasi biomekanik")
    description: Optional[str] = Field(default=None, description="Ringkasan analisis")
    widgets: List[WidgetItem] = Field(description="Daftar widget/chart yang dirender secara dinamis")
    refinement: Optional[RefinementHook] = Field(default=None)

class GenerateRequest(BaseModel):
    prompt: str
    previousContext: Optional[str] = None