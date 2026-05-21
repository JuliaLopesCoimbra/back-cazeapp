-- ============================================
-- Criação da tabela ad_views para tracking de visualizações
-- ============================================

-- Criar a tabela de views
CREATE TABLE IF NOT EXISTS ad_views (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,  -- Referência ao users do auth_db (sem FK pois está em outro banco)
    event_id INTEGER NOT NULL REFERENCES events(id),
    ad_identifier VARCHAR(255) NOT NULL,
    ad_url TEXT,
    viewed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Criar índices básicos
CREATE INDEX IF NOT EXISTS idx_ad_views_user_id ON ad_views(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ad_views_event_id ON ad_views(event_id);
CREATE INDEX IF NOT EXISTS idx_ad_views_viewed_at ON ad_views(viewed_at);
CREATE INDEX IF NOT EXISTS idx_ad_views_ad_identifier ON ad_views(ad_identifier);

-- Índice composto para queries de estatísticas (otimização para alto volume)
-- Este índice já cobre queries por hora de forma eficiente
CREATE INDEX IF NOT EXISTS idx_ad_views_event_ad ON ad_views(event_id, ad_identifier, viewed_at);

-- Comentários nas colunas
COMMENT ON TABLE ad_views IS 'Tabela para armazenar visualizações de anúncios com processamento em batch';
COMMENT ON COLUMN ad_views.user_id IS 'ID do usuário (pode ser NULL para usuários não autenticados)';
COMMENT ON COLUMN ad_views.event_id IS 'ID do evento onde o anúncio foi visualizado';
COMMENT ON COLUMN ad_views.ad_identifier IS 'Identificador único do anúncio (ex: "1", "2", "adplugg_123")';
COMMENT ON COLUMN ad_views.viewed_at IS 'Data e hora da visualização (timezone aware)';

