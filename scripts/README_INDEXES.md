# Script de Otimização de Índices

Este script verifica e cria índices necessários para melhorar a performance das queries.

## Como executar

```bash
cd back-n1
python scripts/check_and_create_indexes.py
```

## Índices que serão criados

### Tabela `likes` (interaction_db)
- `idx_likes_news_id`: Busca rápida de likes por news_id
- `idx_likes_news_user`: Verificação se usuário curtiu (composto)

### Tabela `comments` (interaction_db)
- `idx_comments_news_id`: Busca rápida de comentários por news_id
- `idx_comments_parent_deleted`: Contagem de replies (apenas não deletados)
- `idx_comments_news_parent`: Busca de comentários principais (composto)

### Tabela `comment_likes` (interaction_db)
- `idx_comment_likes_comment_id`: Busca rápida de likes de comentários
- `idx_comment_likes_comment_user`: Verificação se usuário curtiu comentário (composto)

### Tabela `news_posts` (admin_db)
- `idx_news_posts_id_status`: Validação rápida de news (parcial, apenas não deletados)
- `idx_news_posts_event_status`: Busca de news por evento e status (parcial)

## Impacto esperado

Com esses índices, esperamos reduzir:
- **Validação**: De ~388ms para ~50-100ms
- **Likes query**: De ~400ms para ~100-150ms
- **Comments queries**: De ~130ms cada para ~20-50ms cada
- **Total**: De ~1900ms para ~800-1000ms

## Notas

- O script verifica se os índices já existem antes de criar
- Índices parciais (com WHERE) são mais eficientes em espaço
- Execute este script após mudanças no schema do banco

