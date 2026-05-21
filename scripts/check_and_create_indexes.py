"""
Script para verificar e criar índices necessários para otimização de performance.
Execute: python scripts/check_and_create_indexes.py
"""
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config.settings import settings

def check_and_create_indexes():
    """Verifica e cria índices necessários para otimização"""
    
    # Conecta ao banco de interação (onde estão likes e comments)
    interaction_engine = create_engine(
        settings.INTERACTION_DATABASE_URL,
        pool_pre_ping=True,
        echo=False
    )
    
    # Conecta ao banco admin (onde estão news_posts)
    admin_engine = create_engine(
        settings.ADMIN_DATABASE_URL or settings.AUTH_DATABASE_URL,
        pool_pre_ping=True,
        echo=False
    )
    
    indexes_to_create = [
        # Índices para tabela de likes (interaction_db)
        {
            'engine': interaction_engine,
            'table': 'likes',
            'name': 'idx_likes_news_id',
            'columns': 'news_id',
            'description': 'Índice para busca rápida de likes por news_id'
        },
        {
            'engine': interaction_engine,
            'table': 'likes',
            'name': 'idx_likes_news_user',
            'columns': 'news_id, user_id',
            'description': 'Índice composto para verificar se usuário curtiu'
        },
        
        # Índices para tabela de comments (interaction_db)
        {
            'engine': interaction_engine,
            'table': 'comments',
            'name': 'idx_comments_news_id',
            'columns': 'news_id',
            'description': 'Índice para busca rápida de comentários por news_id'
        },
        {
            'engine': interaction_engine,
            'table': 'comments',
            'name': 'idx_comments_parent_deleted',
            'columns': 'parent_comment_id',
            'where': 'deleted_at IS NULL',
            'description': 'Índice parcial para contagem de replies (apenas não deletados)'
        },
        {
            'engine': interaction_engine,
            'table': 'comments',
            'name': 'idx_comments_news_parent',
            'columns': 'news_id, parent_comment_id',
            'where': 'deleted_at IS NULL',
            'description': 'Índice composto para busca de comentários principais'
        },
        
        # Índices para comment_likes (interaction_db)
        {
            'engine': interaction_engine,
            'table': 'comment_likes',
            'name': 'idx_comment_likes_comment_id',
            'columns': 'comment_id',
            'description': 'Índice para busca rápida de likes de comentários'
        },
        {
            'engine': interaction_engine,
            'table': 'comment_likes',
            'name': 'idx_comment_likes_comment_user',
            'columns': 'comment_id, user_id',
            'description': 'Índice composto para verificar se usuário curtiu comentário'
        },
        
        # Índices para news_posts (admin_db)
        {
            'engine': admin_engine,
            'table': 'news_posts',
            'name': 'idx_news_posts_id_status',
            'columns': 'id, status',
            'where': 'deleted_at IS NULL',
            'description': 'Índice parcial para validação rápida de news'
        },
        {
            'engine': admin_engine,
            'table': 'news_posts',
            'name': 'idx_news_posts_event_status',
            'columns': 'event_id, status',
            'where': 'deleted_at IS NULL',
            'description': 'Índice para busca de news por evento e status'
        },
    ]
    
    print("=" * 80)
    print("VERIFICAÇÃO E CRIAÇÃO DE ÍNDICES PARA OTIMIZAÇÃO")
    print("=" * 80)
    print()
    
    for idx_info in indexes_to_create:
        engine = idx_info['engine']
        table = idx_info['table']
        index_name = idx_info['name']
        columns = idx_info['columns']
        description = idx_info.get('description', '')
        where_clause = idx_info.get('where', '')
        
        try:
            with engine.connect() as conn:
                # Verifica se o índice já existe
                check_query = text(f"""
                    SELECT EXISTS (
                        SELECT 1 
                        FROM pg_indexes 
                        WHERE indexname = :index_name
                    )
                """)
                
                result = conn.execute(check_query, {"index_name": index_name})
                exists = result.scalar()
                
                if exists:
                    print(f"✓ Índice '{index_name}' já existe na tabela '{table}'")
                else:
                    # Cria o índice
                    if where_clause:
                        # Índice parcial (com WHERE)
                        create_query = text(f"""
                            CREATE INDEX {index_name} 
                            ON {table} ({columns}) 
                            WHERE {where_clause}
                        """)
                    else:
                        # Índice normal
                        create_query = text(f"""
                            CREATE INDEX {index_name} 
                            ON {table} ({columns})
                        """)
                    
                    conn.execute(create_query)
                    conn.commit()
                    print(f"✓ Criado índice '{index_name}' na tabela '{table}'")
                    if description:
                        print(f"  {description}")
                
        except Exception as e:
            print(f"✗ Erro ao processar índice '{index_name}': {e}")
    
    print()
    print("=" * 80)
    print("VERIFICAÇÃO CONCLUÍDA")
    print("=" * 80)
    
    # Fecha as conexões
    interaction_engine.dispose()
    admin_engine.dispose()

if __name__ == "__main__":
    check_and_create_indexes()

