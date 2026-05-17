"""FastAPI app para RAG-Obras."""
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .routes.ingest import router as ingest_router
from .routes.query import router as query_router
from .routes.logs import router as logs_router
from .routes.storage import router as storage_router

app = FastAPI(title="RAG-Obras API", version="0.1.0")

app.include_router(ingest_router)
app.include_router(query_router)
app.include_router(logs_router)
app.include_router(storage_router)


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