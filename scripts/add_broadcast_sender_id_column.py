"""
Script para adicionar a coluna broadcast_sender_id na tabela notifications
Execute: python scripts/add_broadcast_sender_id_column.py
"""
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.config.notification_db import notification_engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_broadcast_sender_id_column():
    """Adiciona a coluna broadcast_sender_id na tabela notifications"""
    try:
        with notification_engine.connect() as conn:
            # Verificar se a coluna já existe
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'notifications' 
                AND column_name = 'broadcast_sender_id'
            """)
            
            result = conn.execute(check_query)
            exists = result.fetchone()
            
            if exists:
                logger.info("✅ A coluna broadcast_sender_id já existe na tabela notifications")
                return
            
            # Adicionar a coluna
            logger.info("🔄 Adicionando coluna broadcast_sender_id na tabela notifications...")
            alter_query = text("""
                ALTER TABLE notifications 
                ADD COLUMN broadcast_sender_id INTEGER NULL
            """)
            
            conn.execute(alter_query)
            conn.commit()
            
            logger.info("✅ Coluna broadcast_sender_id adicionada com sucesso!")
            
    except Exception as e:
        logger.error(f"❌ Erro ao adicionar coluna: {e}")
        raise

if __name__ == "__main__":
    print()
    print("=" * 60)
    print("Migração: Adicionar coluna broadcast_sender_id")
    print("=" * 60)
    print()
    
    try:
        add_broadcast_sender_id_column()
        print()
        print("✅ Migração concluída com sucesso!")
        print()
    except Exception as e:
        print()
        print(f"❌ Erro na migração: {e}")
        print()
        sys.exit(1)






