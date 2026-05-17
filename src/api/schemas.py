"""Esquemas Pydantic para la API."""
from pydantic import BaseModel


class IngestRequest(BaseModel):
    """Request para /ingest (multipart/form-dataFields)."""
    proyecto_id: int
    nombre: str
    tipo: str  # manual | especificacion | plano | protocolo | cronograma
    sector: str = ""


class IngestResponse(BaseModel):
    """Response de /ingest."""
    documento_id: int
    nombre: str
    chunks_generados: int
    es_imagen: bool
    status: str = "ok"


class ErrorResponse(BaseModel):
    """Response de error."""
    error: str