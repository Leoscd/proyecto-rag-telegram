-- Migration 001: Esquema completo RAG-Obras
-- Idempotente: IF NOT EXISTS en todo.
-- Aplicada en Supabase el 2026-05-17 via MCP.

-- Extensión vector
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabla proyectos
CREATE TABLE IF NOT EXISTS proyectos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    fecha_inicio DATE,
    activo BOOLEAN DEFAULT TRUE
);

-- Tabla documentos
CREATE TABLE IF NOT EXISTS documentos (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER REFERENCES proyectos(id) ON DELETE CASCADE,
    nombre VARCHAR(255) NOT NULL,
    tipo VARCHAR(50),  -- plano, manual, especificacion, protocolo, cronograma
    sector VARCHAR(100),
    ruta_archivo VARCHAR(500),
    texto_extraido TEXT,
    fecha_carga TIMESTAMP DEFAULT NOW()
);

-- Tabla chunks (embeddings vectoriales)
-- vector(3072) = text-embedding-3-large
-- NOTA: pgvector limita índices hnsw/ivfflat a 2000 dims máximo.
-- Con 3072 dims el CREATE INDEX falla. Para el MVP (volumen demo)
-- se usa exact scan (ORDER BY embedding <=> query LIMIT 5).
-- Cuando escale: migrar a halfvec(3072) o reducir a 1536 dims.
CREATE TABLE IF NOT EXISTS chunks (
    id SERIAL PRIMARY KEY,
    documento_id INTEGER REFERENCES documentos(id) ON DELETE CASCADE,
    proyecto_id INTEGER REFERENCES proyectos(id) ON DELETE CASCADE,
    texto TEXT NOT NULL,
    embedding vector(3072),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Tabla consultas (logs RAG)
CREATE TABLE IF NOT EXISTS consultas (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER REFERENCES proyectos(id) ON DELETE CASCADE,
    usuario_telegram VARCHAR(100),
    mensaje_original TEXT NOT NULL,
    respuesta_generada TEXT,
    chunks_usados INTEGER[],
    score_maximo FLOAT,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Índices regulares
CREATE INDEX IF NOT EXISTS idx_documentos_proyecto ON documentos(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_chunks_documento ON chunks(documento_id);
CREATE INDEX IF NOT EXISTS idx_chunks_proyecto ON chunks(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_consultas_proyecto ON consultas(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_consultas_timestamp ON consultas(timestamp);
