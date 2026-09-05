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
    data: Optional[List[ChartDataPoint]] = Field(default=None)
    metricValue: Optional[str] = Field(default=None)
    unit: Optional[str] = Field(default=None)
    bodyPoints: Optional[List[BodyPoint]] = Field(default=None)
    notesContent: Optional[str] = Field(default=None)
    tasks: Optional[List[str]] = Field(default=None)

class WidgetItem(BaseModel):
    id: str = Field(description="ID unik widget")
    type: Literal[
        "TaskTracker", "MarkdownNotes", "MetricCard", 
        "BarChart", "LineChart", "DonutChart", "BodyAnatomyMap"
    ] = Field(description="Tipe chart/widget")
    title: str = Field(description="Judul widget")
    colSpan: int = Field(ge=3, le=12, description="Ukuran lebar grid 12 kolom")
    props: Optional[WidgetProps] = Field(default=None)

class RefinementHook(BaseModel):
    question: str = Field(description="Pertanyaan lanjutan")
    options: List[str] = Field(min_length=2, max_length=3)

class WorkspaceResponse(BaseModel):
    # Parameter penentu validitas topik
    is_clinical_query: bool = Field(description="WAJIB True jika prompt meminta evaluasi klinis/ergonomi serius. WAJIB False jika ini candaan, resep masakan, tugas umum, atau coding.")
    
    workspaceTitle: str = Field(description="Judul evaluasi biomekanik")
    description: Optional[str] = Field(default=None, description="Ringkasan analisis")
    widgets: List[WidgetItem] = Field(description="Daftar widget/chart")
    refinement: Optional[RefinementHook] = Field(default=None)

class GenerateRequest(BaseModel):
    prompt: str
    previousContext: Optional[str] = None