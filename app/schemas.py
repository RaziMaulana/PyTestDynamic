from __future__ import annotations
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class ChartDataPoint(BaseModel):
    label: str = Field(description="Label metrik, fase, atau waktu")
    value: float = Field(description="Nilai numerik metrik")

class BodyPoint(BaseModel):
    part: str = Field(description="Bagian tubuh atau organ yang difokuskan (misal: neck, back, wrists, knees)")
    status: Literal["normal", "warning", "active"] = Field(description="Kondisi visual titik")
    description: str = Field(description="Catatan klinis kondisi organ/sendi")

class WidgetProps(BaseModel):
    data: Optional[List[ChartDataPoint]] = Field(default=None)
    metricValue: Optional[str] = Field(default=None)
    unit: Optional[str] = Field(default=None)
    bodyPoints: Optional[List[BodyPoint]] = Field(default=None)

class WidgetItem(BaseModel):
    id: str = Field(description="ID unik widget, misal: w_1")
    type: Literal[
        "TaskTracker", "MarkdownNotes", "MetricCard", 
        "BarChart", "LineChart", "DonutChart", "BodyAnatomyMap"
    ] = Field(description="Jenis komponen UI")
    title: str = Field(description="Judul widget")
    colSpan: int = Field(ge=3, le=12, description="Ukuran grid 12 kolom")
    props: Optional[WidgetProps] = Field(default=None)

class RefinementHook(BaseModel):
    question: str = Field(description="Pertanyaan tindak lanjut evaluasi klinis")
    options: List[str] = Field(min_length=2, max_length=3, description="2-3 pilihan penyesuaian cepat")

class WorkspaceResponse(BaseModel):
    workspaceTitle: str = Field(description="Judul evaluasi biomekanik")
    description: Optional[str] = Field(default=None, description="Ringkasan evaluasi")
    widgets: List[WidgetItem] = Field(description="Daftar komponen yang dipilih")
    refinement: Optional[RefinementHook] = Field(default=None)

class GenerateRequest(BaseModel):
    prompt: str
    previousContext: Optional[str] = None