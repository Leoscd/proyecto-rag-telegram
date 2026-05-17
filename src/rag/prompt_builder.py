"""Prompt builder para MiniMax."""
from .retriever import ChunkRecuperado


def construir_prompt(
    query: str,
    chunks: list[ChunkRecuperado],
    score_umbral: float = 1.2,
) -> tuple[str, bool]:
    """
    Construye el prompt para MiniMax.
    Retorna (prompt_str, contexto_pobre).
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

    # Prompt base
    prompt = f"""Sos un asistente técnico de obra. Respondé ÚNICAMENTE usando la información
del contexto. Si la información no está en el contexto, decí exactamente:
"No encontré información sobre esto en los documentos disponibles."
No inventes datos, medidas, procedimientos ni normativas.

CONTEXTO:
{contexto}

PREGUNTA: {query}

RESPUESTA:
"""

    # Agregar warning si contexto pobre
    if contexto_pobre:
        prompt += """
ADVERTENCIA: Los documentos disponibles pueden no contener información específica sobre esta consulta.
"""

    return prompt, contexto_pobre