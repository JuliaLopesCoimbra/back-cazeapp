-- Migration: add_event_type_and_world_cup_games
-- Descrição: Adiciona campo event_type na tabela events e cria tabela world_cup_games
-- para suporte a diferentes tipos de evento (carnaval, copa do mundo, etc.)

-- 1. Adiciona event_type na tabela events (default "carnival" para manter compatibilidade)
ALTER TABLE events ADD COLUMN IF NOT EXISTS event_type VARCHAR(50) NOT NULL DEFAULT 'carnival';

-- 2. Define o evento ID 24 como Copa do Mundo
UPDATE events SET event_type = 'world_cup' WHERE id = 24;

-- 3. Cria tabela de jogos da Copa do Mundo
CREATE TABLE IF NOT EXISTS world_cup_games (
    id          SERIAL PRIMARY KEY,
    event_id    INTEGER NOT NULL REFERENCES events(id),
    title       VARCHAR(255) NOT NULL,
    description TEXT,
    photo_url   VARCHAR(500),
    game_date   DATE,
    game_time   TIME,

    created_at    TIMESTAMP DEFAULT NOW(),
    created_by_id INTEGER,
    updated_at    TIMESTAMP,
    updated_by_id INTEGER,

    -- Soft delete
    deleted_at    TIMESTAMP,
    deleted_by_id INTEGER
);

CREATE INDEX IF NOT EXISTS idx_world_cup_games_event_id ON world_cup_games(event_id);
CREATE INDEX IF NOT EXISTS idx_world_cup_games_deleted_at ON world_cup_games(deleted_at);
