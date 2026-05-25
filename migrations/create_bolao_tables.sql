-- Migration: create_bolao_tables
-- Banco: roulette_db
-- Descrição: Módulo Bolão do Placar — Casa CazéTV Copa do Mundo 2026

-- Apostas de placar por usuário por jogo
CREATE TABLE IF NOT EXISTS bolao_predictions (
    id                      SERIAL PRIMARY KEY,
    user_id                 INTEGER NOT NULL,
    fixture_id              INTEGER NOT NULL,
    home_score_prediction   SMALLINT NOT NULL CHECK (home_score_prediction >= 0),
    away_score_prediction   SMALLINT NOT NULL CHECK (away_score_prediction >= 0),
    points_earned           INTEGER NOT NULL DEFAULT 0,
    status                  VARCHAR(20) NOT NULL DEFAULT 'pending'
                                CHECK (status IN ('pending','exact','outcome','wrong','cancelled')),
    settled_at              TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ,
    CONSTRAINT uq_bolao_user_fixture UNIQUE (user_id, fixture_id)
);

CREATE INDEX IF NOT EXISTS idx_bolao_predictions_user_id    ON bolao_predictions(user_id);
CREATE INDEX IF NOT EXISTS idx_bolao_predictions_fixture_id ON bolao_predictions(fixture_id);
CREATE INDEX IF NOT EXISTS idx_bolao_predictions_status     ON bolao_predictions(status);

COMMENT ON TABLE bolao_predictions IS 'Apostas de placar dos usuários nos jogos da Copa 2026';
COMMENT ON COLUMN bolao_predictions.status IS 'pending=aguardando liquidação | exact=placar exato(10pts) | outcome=resultado certo(5pts) | wrong=errou(0pts) | cancelled=cancelado';

-- Catálogo de prêmios resgatáveis com pontos
CREATE TABLE IF NOT EXISTS bolao_prizes (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    image_url       VARCHAR(500),
    total_quantity  INTEGER NOT NULL DEFAULT 0,  -- 0 = ilimitado
    remaining_qty   INTEGER NOT NULL DEFAULT 0,
    points_required INTEGER NOT NULL,
    prize_type      VARCHAR(50) NOT NULL CHECK (prize_type IN ('shirt','ticket','merch','digital')),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE bolao_prizes IS 'Prêmios disponíveis para resgate com pontos do bolão';
COMMENT ON COLUMN bolao_prizes.total_quantity IS '0 = estoque ilimitado';

-- Resgates realizados pelos usuários
CREATE TABLE IF NOT EXISTS bolao_redemptions (
    id           SERIAL PRIMARY KEY,
    user_id      INTEGER NOT NULL,
    prize_id     INTEGER NOT NULL REFERENCES bolao_prizes(id),
    points_spent INTEGER NOT NULL,
    status       VARCHAR(20) NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending','approved','delivered','cancelled')),
    admin_notes  TEXT,
    redeemed_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_bolao_redemptions_user_id  ON bolao_redemptions(user_id);
CREATE INDEX IF NOT EXISTS idx_bolao_redemptions_prize_id ON bolao_redemptions(prize_id);
CREATE INDEX IF NOT EXISTS idx_bolao_redemptions_status   ON bolao_redemptions(status);

COMMENT ON TABLE bolao_redemptions IS 'Histórico de resgates de prêmios pelos usuários';

-- Cache de pontos totais por usuário
CREATE TABLE IF NOT EXISTS bolao_user_points (
    user_id      INTEGER PRIMARY KEY,
    total_points INTEGER NOT NULL DEFAULT 0,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bolao_user_points_total ON bolao_user_points(total_points DESC);

COMMENT ON TABLE bolao_user_points IS 'Pontuação acumulada por usuário — atualizada a cada liquidação';
