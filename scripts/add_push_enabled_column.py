"""
Script para adicionar a coluna push_enabled na tabela notification_preferences.
Execute: python scripts/add_push_enabled_column.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.config.notification_db import notification_engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_push_enabled_column():
    """Adiciona a coluna push_enabled na tabela notification_preferences."""
    try:
        with notification_engine.connect() as conn:
            check_query = text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'notification_preferences'
                AND column_name = 'push_enabled'
            """)
            result = conn.execute(check_query)
            if result.fetchone():
                logger.info("Coluna push_enabled já existe em notification_preferences")
                return
            alter_query = text("""
                ALTER TABLE notification_preferences
                ADD COLUMN push_enabled BOOLEAN NOT NULL DEFAULT FALSE
            """)
            conn.execute(alter_query)
            conn.commit()
            logger.info("Coluna push_enabled adicionada com sucesso.")
    except Exception as e:
        logger.error("Erro ao adicionar coluna push_enabled: %s", e)
        raise


if __name__ == "__main__":
    add_push_enabled_column()
