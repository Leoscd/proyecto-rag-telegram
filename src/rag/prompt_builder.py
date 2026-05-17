"""Prompt builder para MiniMax."""
from .retriever import ChunkRecuperado


def construir_prompt(
    query: str,
    chunks: list[ChunkRecuperado],
    score_umbral: float = 0.6,
) -> tuple[str, bool]:
    """
    Construye el prompt para MiniMax.
    Retorna (prompt_str, contexto_pobre).
    score_umbral=0.6 (distancia coseno: menor = mejor match)
    """
    contexto_pobre = not chunks or (chunks[0].score > score_umbral)

    # Construcción del contexto
    contexto_parts = []
    for chunk in chunks:
        meta = chunk.metadata
        doc_nombre = meta.get("nombre_documento", "documento sin nombre")
        sector = meta.get("sector", "sin sector")
        tipo = meta.get("tipo", "desconocido")

        contexto_parts.append(
            f"--- Documento: {doc_nombre} | Sector: {sector} | Tipo: {tipo} ---\n{chunk.texto}"
        )

    contexto = "\n\n".join(contexto_parts)

    # ADVERTENCIA antes de CONTEXTO si contexto pobre
    advertencia = ""
    if contexto_pobre:
        advertencia = (
            "\nADVERTENCIA: Los documentos disponibles pueden no contener información específica sobre esta consulta.\n"
        )

    # Prompt con ADVERTENCIA antes de CONTEXTO
    prompt = f"""Sos un asistente técnico de obra. Respondé ÚNICAMENTE usando la información
del contexto. Si la información no está en el contexto, decí exactamente:
"No encontré información sobre esto en los documentos disponibles."
No inventes datos, medidas, procedimientos ni normativas.
{advertencia}
CONTEXTO:
{contexto}

PREGUNTA: {query}

RESPUESTA:
"""

    return prompt, contexto_pobre