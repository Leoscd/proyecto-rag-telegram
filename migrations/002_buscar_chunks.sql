-- Migration 002: Función RPC para búsqueda vectorial
-- Ejecutar en SQL Editor de Supabase o con psql

CREATE OR REPLACE FUNCTION buscar_chunks_similares(
    query_vector vector(3072),
    pid integer,
    top_k integer DEFAULT 5
)
RETURNS TABLE(
    id integer,
    texto text,
    metadata jsonb,
    score float
)
LANGUAGE sql STABLE AS $$
    SELECT
        id,
        texto,
        metadata,
        (embedding <=> query_vector)::float AS score
    FROM chunks
    WHERE proyecto_id = pid
    ORDER BY embedding <=> query_vector
    LIMIT top_k;
$$;