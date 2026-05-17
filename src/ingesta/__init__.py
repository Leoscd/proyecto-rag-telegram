"""Módulo de ingesta de documentos."""
from .extractor import extraer, DocumentoExtraido
from .chunker import chunkear, Chunk

__all__ = ["extraer", "DocumentoExtraido", "chunkear", "Chunk"]