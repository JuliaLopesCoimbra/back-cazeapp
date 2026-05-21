-- Migration: add_ticket_url_to_events
-- Descrição: Adiciona campo ticket_url na tabela events para URL de compra de ingressos por evento

ALTER TABLE events ADD COLUMN IF NOT EXISTS ticket_url VARCHAR(500);
