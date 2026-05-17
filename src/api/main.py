"""FastAPI app para RAG-Obras."""
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .routes.ingest import router as ingest_router

app = FastAPI(title="RAG-Obras API", version="0.1.0")

app.include_router(ingest_router)


@app.get("/")
def root():
    """Health check."""
    return {"status": "ok", "servicio": "RAG-Obras API"}


@app.exception_handler(Exception)
def global_exception_handler(request, exc):
    """Manejo global de excepciones — no expone stack traces."""
    return JSONResponse(
        status_code=500,
        content={"error": "Error interno del servidor"},
    )