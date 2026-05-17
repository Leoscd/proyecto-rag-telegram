-- Migration 001: Esquema completo RAG-Obras
-- Idempotente: usar IF NOT EXISTS / IF NOT EXISTS (drop constraint)
-- Ejecutar: psql -h <host> -U <user> -d <db> -f 001_schema.sql

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
CREATE TABLE IF NOT EXISTS chunks (
    id SERIAL PRIMARY KEY,
    documento_id INTEGER REFERENCES documentos(id) ON DELETE CASCADE,
    proyecto_id INTEGER REFERENCES proyectos(id) ON DELETE CASCADE,
    texto TEXT NOT NULL,
    embedding vector(3072),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Tabla consultas (logs)
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

-- Índice vectorial sobre chunks.embedding (coseno)
-- Usamos ivfflat (más liviano para VPS) o hnsw (más rápido)
-- ivfflat requiere datos, hnsw funciona vacío

-- opción 1: ivfflat (clásico, más liviano)
-- CREATE INDEX IF NOT EXISTS idx_chunks_embedding_ivfflat
-- ON chunks USING ivfflat (embedding vector_cosine_ops)
-- WITH (lists = 100);

-- opción 2: hnsw (más rápido, requiere más memoria)
-- HNSW es el default recomendado hoy
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw
ON chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Índices regulares para queries comunes
CREATE INDEX IF NOT EXISTS idx_documentos_proyecto ON documentos(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_chunks_documento ON chunks(documento_id);
CREATE INDEX IF NOT EXISTS idx_chunks_proyecto ON chunks(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_consultas_proyecto ON consultas(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_consultas_timestamp ON consultas(timestamp);