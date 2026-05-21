-- ============================================
-- Criação da tabela face_searches para tracking de buscas de fotos do rosto
-- ============================================

-- Criar a tabela de buscas
CREATE TABLE IF NOT EXISTS face_searches (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,  -- Referência ao users do auth_db (sem FK pois está em outro banco)
    event_id INTEGER NOT NULL REFERENCES events(id),
    collection_id VARCHAR(255) NOT NULL,
    threshold FLOAT,
    max_faces INTEGER,
    face_detected BOOLEAN,
    face_confidence FLOAT,
    matches_count INTEGER DEFAULT 0,
    searched_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Criar índices básicos
CREATE INDEX IF NOT EXISTS idx_face_searches_user_id ON face_searches(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_face_searches_event_id ON face_searches(event_id);
CREATE INDEX IF NOT EXISTS idx_face_searches_searched_at ON face_searches(searched_at);
CREATE INDEX IF NOT EXISTS idx_face_searches_collection_id ON face_searches(collection_id);

-- Índice composto para queries de estatísticas (otimização para alto volume)
CREATE INDEX IF NOT EXISTS idx_face_searches_event_collection ON face_searches(event_id, collection_id, searched_at);

-- Comentários nas colunas
COMMENT ON TABLE face_searches IS 'Tabela para armazenar buscas de fotos do rosto';
COMMENT ON COLUMN face_searches.user_id IS 'ID do usuário que realizou a busca (pode ser NULL para usuários não autenticados)';
COMMENT ON COLUMN face_searches.event_id IS 'ID do evento onde a busca foi realizada';
COMMENT ON COLUMN face_searches.collection_id IS 'ID da coleção do Rekognition usada na busca';
COMMENT ON COLUMN face_searches.searched_at IS 'Data e hora da busca (timezone aware)';




