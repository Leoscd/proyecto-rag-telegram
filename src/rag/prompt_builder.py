"""Prompt builder para RAG-Obras."""
from .retriever import ChunkRecuperado


def construir_prompt(
    query: str,
    chunks: list[ChunkRecuperado],
    similitud_umbral: float = 0.35,
) -> tuple[str, bool]:
    """
    Construye el prompt para el LLM.
    Retorna (prompt_str, contexto_pobre).
    
    Umbral de similitud: 0.35 (mayor = mejor match).
    Si similitud < umbral, contexto_pobre = True.
    """
    if not chunks:
        contexto_pobre = True
        prompt = "Sos un asistente tecnico de obra. No tengo informacion disponible. Respondio: \"No tengo informacion sobre esto en los documentos disponibles.\""
        return prompt, contexto_pobre

    # Convertir distancia a similitud (mayor = mejor)
    distancia = chunks[0].score
    similitud_top = 1.0 - distancia
    contexto_pobre = similitud_top < similitud_umbral

    # Construccion del contexto
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

    # Prompt mejorado: responde con lo que hay, usa "Segun los documentos disponibles"
    prompt = f"""Sos un asistente tecnico de obra que ayuda con la informacion disponible en los planos, manuales y especificaciones del proyecto.

Instructions:
1. Responde usando UNICAMENTE la informacion del contexto de abajo.
2. Si el contexto tiene informacion relacionada pero no completa, responde con lo que si esta disponible usando: "Segun los documentos disponibles, ..." y aclara que parte no figura.
3. Si la informacion del contexto no tiene relacion con la pregunta, responde: "No tengo informacion sobre esto en los documentos disponibles."
4. NO inventes datos, medidas, procedimientos ni normativas que no esten en el contexto.
5. Si hay ambiguedad, explica que dice el documento y que falta.

CONTEXTO:
{contexto}

PREGUNTA: {query}

RESPUESTA:
"""

    return prompt, contexto_pobre