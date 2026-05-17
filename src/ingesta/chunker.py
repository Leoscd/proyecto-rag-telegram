"""Chunker: divide texto en chunks con overlap de tokens."""
import tiktoken
from dataclasses import dataclass
from typing import Any


@dataclass
class Chunk:
    """Un fragmento de documento."""
    texto: str
    tokens: int
    indice: int
    metadata: dict


def chunkear(
    texto: str,
    metadata_base: dict,
    max_tokens: int = 500,
    overlap_tokens: int = 50,
) -> list[Chunk]:
    """
    Divide texto en chunks de max_tokens con overlap_tokens de solape.
    Usa tiktoken con encoding cl100k_base.
    """
    if overlap_tokens >= max_tokens:
        raise ValueError("overlap_tokens debe ser menor que max_tokens")

    if not texto or not texto.strip():
        return []

    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(texto)

    if len(tokens) == 0:
        return []

    # Si cabe en un solo chunk
    if len(tokens) <= max_tokens:
        chunk_texto = enc.decode(tokens)
        return [
            Chunk(
                texto=chunk_texto,
                tokens=len(tokens),
                indice=0,
                metadata={**metadata_base, "chunk_index": 0},
            )
        ]

    chunks = []
    sobre_posicion = overlap_tokens

    inicio = 0
    indice = 0

    while inicio < len(tokens):
        fin = inicio + max_tokens

        # Si es el último chunk y es muy corto, adjuntar al anterior
        if fin >= len(tokens):
            if indice > 0 and len(tokens) - inicio < max_tokens // 4:
                # Si el último chunk es muy pequeno (< 25% del max), merge con anterior
                anterior = chunks[-1]
                nuevo_texto = enc.decode(tokens[inicio:])
                anterior.texto = enc.decode(enc.encode(anterior.texto) + tokens[inicio:])
                anterior.tokens = len(enc.encode(anterior.texto))
                break
            else:
                fin = len(tokens)

        chunk_tokens = tokens[inicio:fin]
        chunk_texto = enc.decode(chunk_tokens)

        chunks.append(
            Chunk(
                texto=chunk_texto,
                tokens=len(chunk_tokens),
                indice=indice,
                metadata={**metadata_base, "chunk_index": indice},
            )
        )

        # Avanzar con overlap
        inicio += max_tokens - overlap_tokens
        indice += 1

    return chunks


def contar_tokens(texto: str) -> int:
    """Cuenta tokens con tiktoken."""
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(texto))