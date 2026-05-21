# Sistema de Tracking de Views de Anúncios - Batch Processing

## 📋 Como Funciona

O sistema de views usa **batch processing** para processar visualizações de forma assíncrona e eficiente:

1. **Frontend** envia view para `/ads/views` → retorna `202 Accepted` imediatamente
2. **Backend** adiciona view à fila em memória (thread-safe)
3. **Worker thread** processa views em lotes:
   - A cada **5 segundos** OU quando a fila atinge **50 views**
   - Faz **bulk insert** no banco (muito mais eficiente)
   - Processa até 50 views por vez

## 🚀 Como Rodar

### 1. Criar a Tabela no Banco de Dados

Execute o SQL no banco `admin_db`:

```bash
# Opção 1: Via psql
psql -h SEU_HOST -U SEU_USUARIO -d SEU_BANCO_ADMIN -f migrations/create_ad_views_table.sql

# Opção 2: Copiar e colar o conteúdo do arquivo SQL no cliente PostgreSQL
```

Ou execute diretamente:

```sql
-- Copie e cole o conteúdo de migrations/create_ad_views_table.sql
```

### 2. O Sistema Já Está Configurado!

O batch processing **inicia automaticamente** quando:
- A primeira view é adicionada à fila
- O worker thread é criado como daemon (não bloqueia o shutdown)

### 3. Verificar se Está Funcionando

Os logs mostrarão:
```
🚀 Batch worker thread iniciado para processamento de views
✅ Processadas 50 views em batch
```

## ⚙️ Configurações

No arquivo `ad_click_controller.py`, você pode ajustar:

```python
_batch_size = 50        # Quantas views processar por vez
_batch_timeout = 5      # Segundos entre processamentos
```

**Recomendações:**
- **5000+ usuários**: Mantenha `batch_size=50` e `timeout=5`
- **Menos usuários**: Pode reduzir para `batch_size=20` e `timeout=10`

## 📊 Monitoramento

### Ver estatísticas de views:
```bash
GET /ads/views/stats?event_id=1
```

### Ver estatísticas de cliques:
```bash
GET /ads/stats?event_id=1
```

## 🔧 Troubleshooting

### Views não estão sendo processadas?

1. Verifique os logs do servidor
2. Confirme que a tabela `ad_views` existe
3. Verifique se há erros no worker thread

### Performance lenta?

1. Aumente `_batch_size` para 100
2. Reduza `_batch_timeout` para 3 segundos
3. Verifique índices do banco de dados

## 📝 Notas Importantes

- ✅ **Thread-safe**: A fila usa locks para evitar race conditions
- ✅ **Auto-start**: Worker inicia automaticamente
- ✅ **Daemon thread**: Não bloqueia shutdown do servidor
- ✅ **Bulk insert**: Muito mais eficiente que inserts individuais
- ✅ **Rate limiting**: 10 views/min por IP (configurável)

## 🎯 Performance Esperada

Com 5000 usuários simultâneos:
- **Views/min**: ~500-1000 views/min
- **Processamento**: 50 views a cada 5s = 600 views/min
- **Latência**: < 5 segundos (tempo de batch)
- **Carga no banco**: Mínima (bulk inserts)




