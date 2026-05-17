"""Esquemas Pydantic para la API."""
from pydantic import BaseModel
from typing import Optional


class IngestRequest(BaseModel):
    """Request para /ingest (multipart/form-data fields)."""
    proyecto_id: int
    nombre: str
    tipo: str
    sector: str = ""


class IngestResponse(BaseModel):
    """Response de /ingest."""
    documento_id: int
    nombre: str
    chunks_generados: int
    es_imagen: bool
    status: str = "ok"


class QueryRequest(BaseModel):
    """Request para /query."""
    proyecto_id: int
    mensaje: str
    usuario_telegram: str


class QueryResponse(BaseModel):
    """Response de /query."""
    respuesta: str
    chunks_usados: list[int]
    score_maximo: float
    contexto_pobre: bool
    tiene_imagen: bool
    ruta_imagen: Optional[str] = None


class LogResponse(BaseModel):
    """Response de /logs."""
    id: int
    proyecto_id: int
    usuario_telegram: str
    mensaje_original: str
    respuesta_generada: str
    chunks_usados: list[int]
    score_maximo: float
    timestamp: str


class ErrorResponse(BaseModel):
    """Response de error."""
    error: str