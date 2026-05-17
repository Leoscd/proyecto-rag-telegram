"""FastAPI app para RAG-Obras."""
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from .routes.ingest import router as ingest_router
from .routes.query import router as query_router
from .routes.logs import router as logs_router
from .routes.storage import router as storage_router
from .routes.proyectos import router as proyectos_router
from .routes.documentos import router as documentos_router
from .routes.stats import router as stats_router

app = FastAPI(title="RAG-Obras API", version="0.1.0")

# Montar archivos estáticos
static_path = Path(__file__).parent.parent / "dashboard"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Registrar routers
app.include_router(ingest_router)
app.include_router(query_router)
app.include_router(logs_router)
app.include_router(storage_router)
app.include_router(proyectos_router)
app.include_router(documentos_router)
app.include_router(stats_router)


@app.get("/")
def root():
    """Health check."""
    return {"status": "ok", "servicio": "RAG-Obras API"}


@app.get("/admin")
def admin_page():
    """Página admin."""
    admin_path = static_path / "admin.html"
    if admin_path.exists():
        return FileResponse(str(admin_path))
    return JSONResponse(status_code=404, content={"error": "Admin no encontrado"})


@app.get("/dashboard")
def dashboard_page():
    """Página del dashboard."""
    dashboard_path = static_path / "index.html"
    if dashboard_path.exists():
        return FileResponse(str(dashboard_path))
    return JSONResponse(status_code=404, content={"error": "Dashboard no encontrado"})


@app.exception_handler(Exception)
def global_exception_handler(request, exc):
    """Manejo global de excepciones."""
    return JSONResponse(
        status_code=500,
        content={"error": "Error interno del servidor"},
    )