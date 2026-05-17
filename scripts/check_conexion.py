#!/usr/bin/env python3
"""Script para verificar conexión a Supabase."""
import sys

try:
    from src.config import get_settings
    from src.db import get_client
except ImportError as e:
    print(f"ERROR: Import fails — {e}")
    sys.exit(1)


def main():
    """Verifica conexión a Supabase."""
    try:
        settings = get_settings()
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    try:
        client = get_client()
        # Query trivial para verificar conexión
        result = client.table("proyectos").select("id").limit(1).execute()
        print("OK: Conexión a Supabase exitosa")
        print(f"   URL: {settings.supabase_url}")
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: Error al conectar a Supabase — {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()