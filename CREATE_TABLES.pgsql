-- Enable the pgvector extension if it's not already enabled.
CREATE EXTENSION IF NOT EXISTS vector;
-- Create a table to store the source documents.
DROP TABLE IF EXISTS public.documents CASCADE;
CREATE TABLE documents (
    doc_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    content TEXT NOT NULL
);
-- Create an index on the document name for faster lookups.
CREATE INDEX idx_documents_name ON documents (name);
-- Create a table to store chunks of the documents.
-- This is useful for breaking down large documents into smaller pieces for embedding.
DROP TABLE IF EXISTS public.document_chunks CASCADE;
CREATE TABLE document_chunks (
    chunk_id UUID DEFAULT gen_random_uuid(),
    doc_id UUID NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    PRIMARY KEY (chunk_id), -- chunk_id is unique, so it can be the primary key.
    -- The original composite key is still unique, but a single-column key on chunk_id is simpler.
    UNIQUE (doc_id, chunk_index), 
    FOREIGN KEY (doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE
);
-- Create an index on the doc_id to quickly retrieve all chunks for a document.
CREATE INDEX idx_document_chunks_doc_id ON document_chunks (doc_id);
-- Create a table to store the vector embeddings for each document chunk.
DROP TABLE IF EXISTS public.embeddings CASCADE;
CREATE TABLE embeddings (
    chunk_id UUID NOT NULL,
    model TEXT NOT NULL,
    task TEXT NOT NULL,
    embedding VECTOR(768) NOT NULL,
    PRIMARY KEY (chunk_id, model, task),
    FOREIGN KEY (chunk_id) REFERENCES document_chunks(chunk_id) ON DELETE CASCADE
);
-- Create HNSW indexes on the embedding column for different distance metrics.
-- Index for Inner Product similarity (<#>)
CREATE INDEX idx_embeddings_embedding_v_ip ON embeddings USING hnsw (embedding vector_ip_ops);
-- Index for Cosine Distance similarity (<=>)
CREATE INDEX idx_embeddings_embedding_v_cosine ON embeddings USING hnsw (embedding vector_cosine_ops);
-- Index for L2 Distance (Euclidean) similarity (<->)
CREATE INDEX idx_embeddings_embedding_v_l2 ON embeddings USING hnsw (embedding vector_l2_ops);