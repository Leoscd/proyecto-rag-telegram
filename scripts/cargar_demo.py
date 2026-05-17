"""Script para cargar documentos de demo al sistema."""
import httpx
from pathlib import Path

API_URL = "http://localhost:8000"
DEMO_DIR = Path("data/demo")

DOCUMENTOS = [
    {
        "archivo": "manual_seguridad_encofrados.pdf",
        "nombre": "Manual de seguridad — Encofrados",
        "tipo": "manual",
        "sector": "general",
    },
    {
        "archivo": "especificacion_tecnica_columnas.pdf",
        "nombre": "Especificación técnica — Columnas",
        "tipo": "especificacion",
        "sector": "norte",
    },
    {
        "archivo": "plano_columna_sector_norte.png",
        "nombre": "Plano columna sector norte",
        "tipo": "plano",
        "sector": "norte",
    },
]


def cargar_todos():
    """Carga los documentos de demo."""
    print("🏗️ Cargando documentos de demo...")
    
    with httpx.Client(timeout=120.0) as client:
        # Crear proyecto demo
        resp = client.post(
            f"{API_URL}/proyectos",
            json={
                "nombre": "Edificio Central Demo",
                "descripcion": "Proyecto demo para pitch TIIC",
                "fecha_inicio": "2026-01-01"
            }
        )
        
        if resp.status_code == 201:
            proyecto_id = resp.json()["id"]
            print(f"✅ Proyecto creado: id={proyecto_id}")
        else:
            # Proyecto ya existe, usar id=1
            proyecto_id = 1
            print(f"ℹ️ Usando proyecto_id={proyecto_id}")

        # Ingestar documentos
        for doc in DOCUMENTOS:
            archivo_path = DEMO_DIR / doc["archivo"]
            if not archivo_path.exists():
                print(f"⚠️ No encontrado: {archivo_path} — saltando")
                continue

            print(f"📤 Cargando: {doc['nombre']}...")
            
            with open(archivo_path, "rb") as f:
                files = {"archivo": (doc["archivo"], f.read(), "application/pdf")}
                data = {
                    "proyecto_id": str(proyecto_id),
                    "nombre": doc["nombre"],
                    "tipo": doc["tipo"],
                    "sector": doc["sector"],
                }
                
                resp = client.post(f"{API_URL}/ingest", files=files, data=data)

            if resp.status_code == 200:
                r = resp.json()
                print(f"  ✅ {r['nombre']} — {r['chunks_generados']} chunks, imagen={r['es_imagen']}")
            else:
                print(f"  ❌ Error: {resp.text[:200]}")
        
        print("🎉 Carga completa!")


if __name__ == "__main__":
    cargar_todos()