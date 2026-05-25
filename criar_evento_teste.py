import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
from app.config.settings import settings

engine = create_engine(
    settings.ADMIN_DATABASE_URL,
    connect_args={"sslmode": settings.DB_SSLMODE}
)

starts_at = datetime.now() + timedelta(days=7)
ends_at = datetime.now() + timedelta(days=8)

with engine.connect() as conn:
    result = conn.execute(text("""
        INSERT INTO events (
            title, event_type, brand_key, description, location,
            starts_at, ends_at, is_active, requires_post_approval,
            created_at
        ) VALUES (
            'Evento Teste', 'carnival', 'default', 'Evento criado para testes',
            'São Paulo - SP', :starts_at, :ends_at, true, false, now()
        )
        RETURNING id, title, is_active, starts_at
    """), {"starts_at": starts_at, "ends_at": ends_at})
    conn.commit()
    row = result.fetchone()
    print(f"Evento criado com sucesso!")
    print(f"  ID: {row[0]}")
    print(f"  Título: {row[1]}")
    print(f"  Ativo: {row[2]}")
    print(f"  Início: {row[3]}")
