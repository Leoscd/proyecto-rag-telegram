"""RAG package."""
from .retriever import ChunkRecuperado, recuperar
from .prompt_builder import construir_prompt

__all__ = ["ChunkRecuperado", "recuperar", "construir_prompt"]