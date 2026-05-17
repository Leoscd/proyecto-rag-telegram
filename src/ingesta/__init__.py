"""Módulo de ingesta de documentos."""
from .extractor import extraer, DocumentoExtraido
from .chunker import chunkear, Chunk
from .embedder import embeder_y_guardar

__all__ = ["extraer", "DocumentoExtraido", "chunkear", "Chunk", "embeder_y_guardar"]