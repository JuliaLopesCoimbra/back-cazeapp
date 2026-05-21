# CLAUDE.md — Backend · Casa CazéTV Copa 2026

> Guia autoritativo para o Claude Code CLI no projeto **back-end/back-cazeapp**.
> Leia por completo antes de tocar em qualquer arquivo. Regras são não-negociáveis.

---

## Índice

1. [Stack e Dependências](#1-stack-e-dependências)
2. [Arquitetura de Domínios](#2-arquitetura-de-domínios)
3. [Padrão de um Domínio](#3-padrão-de-um-domínio)
4. [Banco de Dados](#4-banco-de-dados)
5. [Schemas Pydantic — Regras Estritas](#5-schemas-pydantic--regras-estritas)
6. [Camada de Serviço](#6-camada-de-serviço)
7. [Routers FastAPI](#7-routers-fastapi)
8. [Autenticação e Autorização](#8-autenticação-e-autorização)
9. [Redis e Cache](#9-redis-e-cache)
10. [Celery — Background Tasks](#10-celery--background-tasks)
11. [Tratamento de Erros](#11-tratamento-de-erros)
12. [Testes](#12-testes)
13. [Segurança](#13-segurança)
14. [Variáveis de Ambiente](#14-variáveis-de-ambiente)

---

## 1. Stack e Dependências

```
Python        3.10+
FastAPI       latest         Framework web
Uvicorn       latest         ASGI server
Gunicorn      latest         Process manager (produção)
SQLAlchemy    2.x            ORM (async)
Alembic       latest         Migrations
Pydantic      v2             Validação e serialização
Redis         latest         Cache e session store
Celery        latest         Background tasks
PyJWT         latest         JWT
Bcrypt        latest         Hash de senhas
Pillow        latest         Processamento de imagem
Boto3         latest         AWS SDK (S3, Rekognition, CloudFront)
httpx         latest         HTTP client async (para API-Sports)
pytest        latest         Testes
pytest-asyncio latest        Testes assíncronos
```

### Dependências dos novos módulos

```bash
# Nenhuma nova dependência necessária — todos os pacotes já estão em requirements.txt
# Apenas criar os novos módulos dentro da estrutura existente
```

---

## 2. Arquitetura de Domínios

### Princípio: Domain-Driven Design

Cada funcionalidade é um **domínio isolado** dentro de `app/domain/`. Um domínio não importa de outro domínio diretamente — comunicação acontece via services ou eventos Celery.

```
app/domain/
├── auth/           # Autenticação — NÃO ALTERAR
├── admin/          # Eventos, notícias, produtos — ADAPTAR (novo theme, POIs)
├── football/       # API-Sports — ATUALIZAR season para 2026
├── photo_ai/       # Rekognition — NÃO ALTERAR
├── bolao/          # NOVO — apostas, pontos, prêmios, resgates
├── stickers/       # NOVO — álbum, pacotes, trocas
└── venue_map/      # NOVO — POIs do mapa interativo
```

### Dependências permitidas entre domínios

```
bolao     → pode ler de football (fixture_id é referência externa, não FK)
bolao     → pode chamar stickers.service para distribuir pacotes como recompensa
stickers  → NÃO depende de nenhum outro domínio de negócio
venue_map → NÃO depende de nenhum outro domínio de negócio
admin     → pode ler de qualquer domínio para montar dashboards
```

---

## 3. Padrão de um Domínio

Todo domínio **DEVE** ter exatamente esta estrutura:

```
app/domain/bolao/
├── __init__.py
├── models.py      # SQLAlchemy ORM models
├── schemas.py     # Pydantic v2 schemas (Request, Response, Internal)
├── service.py     # Toda a lógica de negócio
├── router.py      # Endpoints FastAPI (apenas HTTP concerns)
└── exceptions.py  # Exceções customizadas do domínio (opcional)
```

### `models.py` — padrão obrigatório

```python
# app/domain/bolao/models.py
from sqlalchemy import Column, String, Integer, SmallInteger, DateTime, text, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.config.database import RouletteBase  # base do banco correto
import uuid

class BolaoPredicition(RouletteBase):
    __tablename__ = "bolao_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    fixture_id = Column(Integer, nullable=False, index=True)
    home_score_prediction = Column(SmallInteger, nullable=False)
    away_score_prediction = Column(SmallInteger, nullable=False)
    points_earned = Column(Integer, nullable=False, server_default="0")
    status = Column(
        String,
        nullable=False,
        server_default="pending",
        info={"check": "status IN ('pending','exact','outcome','wrong','cancelled')"}
    )
    settled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False)

    __table_args__ = (
        CheckConstraint("home_score_prediction >= 0", name="ck_home_score_non_negative"),
        CheckConstraint("away_score_prediction >= 0", name="ck_away_score_non_negative"),
        CheckConstraint("status IN ('pending','exact','outcome','wrong','cancelled')", name="ck_prediction_status"),
        {"schema": None},
    )
```

**Regras de models:**
- Primary key sempre `UUID` com `default=uuid.uuid4`
- `created_at` com `server_default=text("now()")` — gerado pelo banco
- `updated_at` com `onupdate=text("now()")` — atualizado automaticamente
- Constraints de check duplicados no Python e no SQL das migrations
- Índices em todas as colunas usadas em filtros frequentes: `user_id`, `fixture_id`, `status`

### `schemas.py` — padrão obrigatório

```python
# app/domain/bolao/schemas.py
from pydantic import BaseModel, Field, field_validator, UUID4
from datetime import datetime
from typing import Optional

# ----- Request schemas (entram na API) -----

class CreatePredictionRequest(BaseModel):
    fixture_id: int = Field(..., gt=0, description="ID do fixture na API-Sports")
    home_score_prediction: int = Field(..., ge=0, le=30)
    away_score_prediction: int = Field(..., ge=0, le=30)

class RedeemPrizeRequest(BaseModel):
    prize_id: UUID4

# ----- Response schemas (saem da API) -----

class PredictionResponse(BaseModel):
    id: UUID4
    fixture_id: int
    home_score_prediction: int
    away_score_prediction: int
    points_earned: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}  # Pydantic v2 — habilita ORM mode

class RankingEntryResponse(BaseModel):
    rank: int
    user_id: UUID4
    display_name: str
    avatar_url: Optional[str]
    total_points: int
    exact_predictions: int
    correct_outcomes: int

# ----- Internal schemas (dentro do service, nunca saem na API) -----

class SettlePredictionsPayload(BaseModel):
    fixture_id: int
    actual_home_score: int
    actual_away_score: int
```

**Regras de schemas:**
- `model_config = {"from_attributes": True}` em **todo** schema de Response que lê do ORM
- `Field(...)` com validações explícitas em todo campo de Request
- Nunca retornar schema interno (`Internal`) em endpoint — só `Response`
- Separar claramente `Request`, `Response` e `Internal` por comentário ou subclasses

---

## 4. Banco de Dados

### Mapeamento domínio → banco

| Domínio | Banco (engine) | Constante Base |
|---|---|---|
| auth | `auth_db` | `AuthBase` |
| admin, venue_map | `admin_db` | `AdminBase` |
| interaction | `interaction_db` | `InteractionBase` |
| bolao | `roulette_db` | `RouletteBase` |
| notifications | `notifications_db` | `NotificationBase` |
| photo_ai | `photo_ai_db` | `PhotoAIBase` |
| **stickers** | **`stickers_db`** (NOVO) | **`StickersBase`** |

### Adicionar `stickers_db` ao `config/database.py`

```python
# Adicionar no final do arquivo database.py existente

STICKERS_DATABASE_URL = settings.stickers_database_url

stickers_engine = create_engine(
    STICKERS_DATABASE_URL,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,
)

StickersSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=stickers_engine)

class StickersBase(DeclarativeBase):
    pass

def get_stickers_db():
    db = StickersSessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Regras de banco de dados

1. **Zero raw SQL nos services** — apenas SQLAlchemy ORM queries
2. **Queries N+1 são proibidas** — usar `joinedload` ou `selectinload` para relations
3. **Transações explícitas** para operações que tocam mais de uma tabela

```python
# CORRETO — transação explícita para troca de figurinhas
def accept_sticker_trade(db: Session, trade_id: UUID, receiver_id: UUID) -> None:
    with db.begin():  # transação explícita
        trade = db.query(StickerTrade).filter_by(id=trade_id).with_for_update().first()
        if not trade or trade.status != 'open':
            raise TradeNotAvailableError()
        # validar e executar troca atomicamente
        _transfer_sticker(db, from_user=trade.offerer_id, to_user=receiver_id, sticker_id=trade.offered_sticker_id)
        _transfer_sticker(db, from_user=receiver_id, to_user=trade.offerer_id, sticker_id=trade.wanted_sticker_id)
        trade.status = 'accepted'
        trade.resolved_at = datetime.utcnow()
        trade.receiver_id = receiver_id
```

4. **`with_for_update()`** em operações concorrentes: abrir pacote, aceitar troca, resgatar prêmio
5. **Soft delete** (`is_active = False`) onde já existe no projeto — não usar `DELETE` nas entidades principais
6. **Índices obrigatórios** — ao criar tabela nova, mapear todos os campos usados em `WHERE`, `ORDER BY` e `JOIN`

### Migrations — Alembic

```bash
# Gerar nova migration
alembic revision --autogenerate -m "create_bolao_tables"

# Aplicar
alembic upgrade head

# Rollback
alembic downgrade -1
```

**Regras de migration:**
- Arquivos são **append-only** — nunca editar migration já aplicada em produção
- Nomear descritivamente: `0015_create_bolao_tables`, `0016_create_stickers_tables`
- Toda migration **deve** ter `downgrade()` implementado
- Constraints CHECK duplicadas no Python (model) e na migration SQL

---

## 5. Schemas Pydantic — Regras Estritas

1. **Pydantic v2** — usar `model_config`, `field_validator`, `model_validator` (não v1 compat)
2. **Nunca retornar dict raw** do SQLAlchemy — sempre mapear para Response schema
3. **`model_config = {"from_attributes": True}`** em todo schema que lê de ORM model
4. Validações de negócio nos schemas de Request (range, formato) — validações de estado nos services
5. Sem `Optional` sem motivo — campo opcional é explícito com default `None`

```python
# CORRETO
class CreatePredictionRequest(BaseModel):
    fixture_id: int = Field(..., gt=0)
    home_score_prediction: int = Field(..., ge=0, le=30)
    away_score_prediction: int = Field(..., ge=0, le=30)

# ERRADO — sem validações
class CreatePredictionRequest(BaseModel):
    fixture_id: int
    home_score_prediction: int
    away_score_prediction: int
```

---

## 6. Camada de Serviço

### Regras absolutas do service

1. **Zero lógica de HTTP nos services** — services não sabem que existem routers
2. **Funções puras para lógica de cálculo** — sem side effects, sem acesso a DB

```python
# app/domain/bolao/service.py

# CORRETO — função pura para calcular pontos
def calculate_points(
    predicted_home: int,
    predicted_away: int,
    actual_home: int,
    actual_away: int,
) -> tuple[int, str]:
    if predicted_home == actual_home and predicted_away == actual_away:
        return 10, 'exact'
    predicted_outcome = _outcome(predicted_home, predicted_away)
    actual_outcome = _outcome(actual_home, actual_away)
    if predicted_outcome == actual_outcome:
        return 5, 'outcome'
    return 0, 'wrong'

def _outcome(home: int, away: int) -> str:
    if home > away: return 'home'
    if away > home: return 'away'
    return 'draw'
```

3. **Type annotations completas** em todos os parâmetros e retornos
4. **Raise exceções customizadas** do domínio — nunca `HTTPException` no service

```python
# app/domain/bolao/exceptions.py
class BettingClosedError(Exception):
    """Raised when user tries to bet after betting_closes_at"""

class InsufficientPointsError(Exception):
    """Raised when user doesn't have enough points for redemption"""

class PrizeOutOfStockError(Exception):
    """Raised when prize quantity reaches zero"""
```

5. **Idempotência** — `create_or_update_prediction` não falha se já existe, atualiza

### Padrão de função de service

```python
# Assinatura padronizada
def get_ranking(
    db: Session,
    limit: int = 50,
    offset: int = 0,
) -> list[RankingEntryResponse]:
    ...

def create_or_update_prediction(
    db: Session,
    user_id: UUID,
    payload: CreatePredictionRequest,
) -> PredictionResponse:
    ...

def settle_predictions(
    db: Session,
    fixture_id: int,
    actual_home: int,
    actual_away: int,
) -> int:  # retorna número de apostas liquidadas
    ...
```

---

## 7. Routers FastAPI

### Responsabilidade do router

O router **APENAS** faz:
1. Definir path, método HTTP e status code
2. Injetar dependências (DB, usuário autenticado)
3. Chamar o service
4. Converter exceções de domínio para `HTTPException`
5. Retornar o response schema

O router **NUNCA** faz:
- Queries de banco diretamente
- Lógica de negócio
- Múltiplas chamadas de service sem orquestração

```python
# app/domain/bolao/router.py
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_roulette_db
from app.core.security import get_current_user
from app.domain.bolao import service
from app.domain.bolao.schemas import CreatePredictionRequest, PredictionResponse, RankingEntryResponse
from app.domain.bolao.exceptions import BettingClosedError, InsufficientPointsError, PrizeOutOfStockError

router = APIRouter(prefix="/bolao", tags=["bolao"])

@router.post(
    "/predictions",
    response_model=PredictionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_prediction(
    payload: CreatePredictionRequest,
    db: Session = Depends(get_roulette_db),
    current_user = Depends(get_current_user),
):
    try:
        return service.create_or_update_prediction(db, current_user.id, payload)
    except BettingClosedError:
        raise HTTPException(status_code=400, detail="Apostas encerradas para este jogo")

@router.get(
    "/ranking",
    response_model=list[RankingEntryResponse],
)
def get_ranking(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_roulette_db),
    _: None = Depends(get_current_user),  # autenticado mas não usa o user
):
    return service.get_ranking(db, limit=limit, offset=offset)
```

### Convenções de routers

- `prefix` e `tags` definidos no router, não no `main.py`
- `response_model` explícito em **todo** endpoint que retorna dados
- `status_code` explícito em endpoints de criação (`201`) e deleção (`204`)
- Parâmetros de query com `Query(default, ge=0, le=100)` quando aplicável
- Rota de admin sempre protegida por `Depends(require_admin_role)`

### Montagem em `main.py`

```python
# Adicionar ao final do bloco de routers em main.py
from app.domain.bolao.router import router as bolao_router
from app.domain.stickers.router import router as stickers_router
from app.domain.venue_map.router import router as venue_map_router

app.include_router(bolao_router)
app.include_router(stickers_router)
app.include_router(venue_map_router)
```

---

## 8. Autenticação e Autorização

### Reutilizar sem alteração

Todo o sistema de auth existente (`app/core/security.py`, `app/domain/auth/`) **NÃO DEVE SER ALTERADO**.

### Dependências disponíveis

```python
from app.core.security import get_current_user, require_admin_role

# Endpoint autenticado (qualquer usuário logado)
@router.get("/my-points")
def get_my_points(current_user = Depends(get_current_user)):
    ...

# Endpoint admin only
@router.post("/prizes")
def create_prize(
    payload: CreatePrizeRequest,
    current_user = Depends(require_admin_role),
):
    ...
```

### Regras de autorização por módulo

| Endpoint | Autenticação | Role |
|---|---|---|
| `GET /bolao/fixtures` | Obrigatória | Qualquer user |
| `POST /bolao/predictions` | Obrigatória | Qualquer user |
| `GET /bolao/ranking` | Obrigatória | Qualquer user |
| `GET /bolao/prizes` | Obrigatória | Qualquer user |
| `POST /bolao/prizes` | Obrigatória | admin_master, subadmin |
| `POST /bolao/redeem` | Obrigatória | Qualquer user |
| `POST /bolao/settle/{fixture_id}` | Obrigatória | admin_master (ou Celery) |
| `GET /stickers/album` | Obrigatória | Qualquer user |
| `POST /stickers/packs/*/open` | Obrigatória | Dono do pack |
| `POST /stickers/checkin` | Obrigatória | Qualquer user |
| `POST /stickers/trades/*/accept` | Obrigatória | receiver_id == current_user |
| `GET /venue-map/pois` | Obrigatória | Qualquer user |
| `POST /venue-map/pois` | Obrigatória | admin_master, subadmin |

---

## 9. Redis e Cache

### Quando usar cache

| Dado | TTL | Justificativa |
|---|---|---|
| Fixtures da Copa (API-Sports) | 5 min | API externa tem rate limit |
| Placar ao vivo | 30s | Dado muda frequentemente durante jogo |
| Ranking do bolão | 60s | Aceita eventual consistency |
| Catálogo de prêmios | 5 min | Muda raramente |
| POIs do mapa | 10 min | Muda raramente |
| Álbum de figurinhas do usuário | 30s | Muda após abertura de pacote |

### Padrão de cache com Redis

```python
# app/infra/cache.py — usar o cliente Redis existente

from app.infra.redis_client import redis_client
import json
from typing import Optional, Callable, TypeVar
import functools

T = TypeVar('T')

async def get_or_set_cache(
    key: str,
    fetch_fn: Callable[[], T],
    ttl_seconds: int,
) -> T:
    cached = await redis_client.get(key)
    if cached:
        return json.loads(cached)
    
    value = fetch_fn()
    await redis_client.setex(key, ttl_seconds, json.dumps(value, default=str))
    return value
```

### Cache keys — convenção

```python
# Prefixo por domínio para evitar colisões
CACHE_KEYS = {
    "fixtures":          "football:fixtures:{season}",
    "live_fixtures":     "football:fixtures:live",
    "fixture_by_id":     "football:fixture:{fixture_id}",
    "bolao_ranking":     "bolao:ranking:{limit}:{offset}",
    "bolao_prizes":      "bolao:prizes",
    "venue_pois":        "venue:pois:{city}",
    "sticker_catalog":   "stickers:catalog",
}
```

### Invalidação de cache

Após mutations que afetam dados cacheados, invalidar explicitamente:

```python
# Após liquidar apostas — invalida ranking
await redis_client.delete(f"bolao:ranking:*")  # ou usar scan + delete

# Após admin criar/editar POI — invalida cache do mapa
await redis_client.delete(f"venue:pois:SP")
await redis_client.delete(f"venue:pois:RJ")
```

---

## 10. Celery — Background Tasks

### Tasks críticas dos novos módulos

**`settle_bolao_predictions`** — liquidar apostas quando jogo termina

```python
# app/domain/bolao/tasks.py
from app.config.celery_app import celery_app
from app.config.database import get_roulette_db_context
from app.domain.bolao import service as bolao_service
from app.domain.stickers import service as sticker_service

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def settle_bolao_predictions(self, fixture_id: int, actual_home: int, actual_away: int):
    try:
        with get_roulette_db_context() as db:
            count = bolao_service.settle_predictions(db, fixture_id, actual_home, actual_away)
            # Distribuir pacotes de recompensa
            winners = bolao_service.get_exact_winners(db, fixture_id)
            with get_stickers_db_context() as stickers_db:
                for user_id in winners:
                    sticker_service.grant_pack(stickers_db, user_id, "bolao_reward", quantity=3)
    except Exception as exc:
        raise self.retry(exc=exc)
```

**`check_finished_fixtures`** — polling para detectar jogos finalizados

```python
@celery_app.task
def check_finished_fixtures():
    """Roda a cada 5 minutos via Celery Beat para detectar jogos terminados"""
    # 1. Buscar fixtures com apostas pendentes no bolão
    # 2. Para cada fixture, checar status na API-Sports (usar cache Redis de 30s)
    # 3. Se status == 'FT' (Full Time): disparar settle_bolao_predictions
    ...
```

**`expire_sticker_trades`** — expirar trocas vencidas

```python
@celery_app.task
def expire_sticker_trades():
    """Roda 1x por dia via Celery Beat"""
    ...
```

### Configuração Celery Beat para novas tasks

```python
# Adicionar ao celery_app.py existente
beat_schedule = {
    # Existentes...
    
    # NOVOS
    'check-finished-fixtures': {
        'task': 'app.domain.bolao.tasks.check_finished_fixtures',
        'schedule': 300.0,  # a cada 5 minutos
    },
    'expire-sticker-trades': {
        'task': 'app.domain.stickers.tasks.expire_sticker_trades',
        'schedule': 86400.0,  # diariamente
    },
}
```

### Regras de tasks Celery

- `bind=True` + `max_retries=3` em tasks que chamam serviços externos
- Retry com `default_retry_delay` exponencial para evitar thundering herd
- Tasks **não** retornam dados ao caller — são fire-and-forget
- Tasks que acessam DB usam context managers, não Depends()

---

## 11. Tratamento de Erros

### Hierarquia de exceções

```
Exception
├── BolaoError
│   ├── BettingClosedError         → HTTP 400
│   ├── InsufficientPointsError    → HTTP 400
│   ├── PrizeOutOfStockError       → HTTP 400
│   └── AlreadyBetError            → HTTP 409
├── StickersError
│   ├── PackAlreadyOpenedError     → HTTP 400
│   ├── TradeNotAvailableError     → HTTP 400
│   ├── InsufficientStickersError  → HTTP 400
│   └── CheckInAlreadyUsedError    → HTTP 409
└── VenueMapError
    └── POINotFoundError           → HTTP 404
```

### Mapeamento no router (padrão)

```python
# Bloco try/except padrão no router
try:
    return service.accept_sticker_trade(db, trade_id, current_user.id)
except TradeNotAvailableError:
    raise HTTPException(status_code=400, detail="Troca não está mais disponível")
except InsufficientStickersError:
    raise HTTPException(status_code=400, detail="Você não possui a figurinha necessária para a troca")
except Exception:
    raise HTTPException(status_code=500, detail="Erro interno. Tenta de novo!")
```

### Respostas de erro padronizadas

```python
# Todas as respostas de erro seguem este formato
{
    "detail": "Mensagem amigável em português"
}
```

Mensagens de erro na API também seguem o tom de voz Cazé TV quando expostas ao usuário final.

---

## 12. Testes

### Cobertura obrigatória — endpoints críticos

Os testes de integração **devem** cobrir obrigatoriamente:

| Módulo | Casos de teste obrigatórios |
|---|---|
| **Bolão** | Criar aposta válida; criar aposta após deadline (deve falhar); liquidar apostas (placar exato, resultado certo, errado); verificar pontos após liquidação; resgatar prêmio com pontos suficientes; resgatar sem pontos (deve falhar) |
| **Figurinhas** | Abrir pacote diário; tentar abrir segundo pacote no mesmo dia (deve falhar); criar oferta de troca; aceitar troca (validar que ambos perderam/ganharam corretamente); check-in presencial com código válido; check-in com código repetido (deve falhar) |
| **Auth** | Reutilizar testes existentes — não alterar |

### Estrutura dos testes

```python
# tests/domain/bolao/test_predictions.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.fixtures import create_test_user, create_test_fixture_in_db

client = TestClient(app)

class TestCreatePrediction:
    def test_create_valid_prediction(self, auth_headers, db_session):
        fixture = create_test_fixture_in_db(db_session, status="NS")
        response = client.post(
            "/bolao/predictions",
            json={"fixture_id": fixture.fixture_id, "home_score_prediction": 2, "away_score_prediction": 1},
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["status"] == "pending"

    def test_cannot_bet_after_deadline(self, auth_headers, db_session):
        fixture = create_test_fixture_in_db(db_session, status="1H")  # jogo em andamento
        response = client.post(
            "/bolao/predictions",
            json={"fixture_id": fixture.fixture_id, "home_score_prediction": 1, "away_score_prediction": 0},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "encerradas" in response.json()["detail"]

class TestSettlePredictions:
    def test_exact_score_gives_10_points(self, db_session, admin_headers):
        # Setup: criar aposta com 2x1
        # Action: liquidar com resultado 2x1
        # Assert: 10 pontos, status 'exact'
        ...

    def test_correct_outcome_gives_5_points(self, db_session, admin_headers):
        # Setup: apostar 3x1 (Brasil ganha)
        # Action: resultado 1x0 (Brasil ganha)
        # Assert: 5 pontos, status 'outcome'
        ...
```

### Fixtures de teste

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.database import RouletteBase

TEST_ROULETTE_DB = "postgresql://test:test@localhost/test_roulette_db"

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(TEST_ROULETTE_DB)
    RouletteBase.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()
    RouletteBase.metadata.drop_all(engine)

@pytest.fixture
def auth_headers(db_session):
    user = create_test_user(db_session)
    token = generate_test_token(user.id)
    return {"Authorization": f"Bearer {token}"}
```

### Executar testes

```bash
cd back-end/back-cazeapp
pytest tests/domain/bolao/ -v
pytest tests/domain/stickers/ -v
pytest tests/ -v --tb=short          # todos os testes
```

---

## 13. Segurança

### Regras absolutas

1. **SUPABASE_SERVICE_KEY / JWT secrets** nunca são logados, nunca vão em response
2. **`user_id` de toda aposta/pack/troca** é sempre extraído do JWT, nunca aceito no body

```python
# CORRETO — user_id vem do token
@router.post("/predictions")
def create_prediction(
    payload: CreatePredictionRequest,  # sem user_id no payload
    current_user = Depends(get_current_user),  # user_id vem daqui
):
    return service.create_or_update_prediction(db, current_user.id, payload)

# ERRADO — nunca aceitar user_id do cliente
class CreatePredictionRequest(BaseModel):
    user_id: UUID4  # NUNCA — manipulável pelo cliente
    fixture_id: int
```

3. **Rate limiting** nos endpoints de abertura de pacotes e apostas — usar Redis counter

```python
# app/core/rate_limit.py — criar se não existir
async def check_rate_limit(user_id: UUID, action: str, max_calls: int, window_seconds: int):
    key = f"rate:{action}:{user_id}"
    count = await redis_client.incr(key)
    if count == 1:
        await redis_client.expire(key, window_seconds)
    if count > max_calls:
        raise HTTPException(status_code=429, detail="Muitas tentativas. Aguarde um momento! 😅")
```

4. **Validação de posse** antes de toda operação de troca — verificar que o usuário possui a figurinha oferecida
5. **`with_for_update()`** em operações concorrentes para evitar race conditions em resgates de prêmio limitados
6. **Checkin codes** assinados com HMAC usando `BOLAO_CHECKIN_SECRET` — nunca código sequencial ou previsível

### CORS

```python
# main.py — configuração CORS obrigatória
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),  # lista de domínios do .env
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

## 14. Variáveis de Ambiente

```bash
# back-end/back-cazeapp/.env

# ===== EXISTENTES — não alterar =====
AUTH_DATABASE_URL=postgresql://...
ADMIN_DATABASE_URL=postgresql://...
INTERACTION_DATABASE_URL=postgresql://...
ROULETTE_DATABASE_URL=postgresql://...
NOTIFICATIONS_DATABASE_URL=postgresql://...
JWT_SECRET=...
JWT_REFRESH_SECRET=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
FB_CLIENT_ID=...
FB_CLIENT_SECRET=...
AWS_ACCESS_KEY=...
AWS_SECRET_KEY=...
AWS_REGION=sa-east-1
AWS_BUCKET=...
AWS_CLOUDFRONT_DOMAIN=...
REKOGNITION_COLLECTION=...
ONESIGNAL_APP_ID=...
ONESIGNAL_API_KEY=...
REDIS_URL=redis://...
SMTP_HOST=...
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...

# ===== ATUALIZAR =====
APISPORTS_KEY=...
APISPORTS_WC_SEASON=2026        # ERA 2022 — OBRIGATÓRIO atualizar

# ===== NOVOS =====
STICKERS_DATABASE_URL=postgresql://user:pass@host:5432/stickers_db
BOLAO_CHECKIN_SECRET=...         # segredo HMAC para assinar códigos de check-in QR
ALLOWED_ORIGINS=http://localhost:3000,https://cazetv-copa.vercel.app
```

### Validação no boot — obrigatória

Usar `pydantic-settings` (já em uso no projeto) para validar presença de todas as env vars no startup. Não deixar o app subir com vars faltando.

---

## Quick Reference — Convenções Python

| Item | Convenção | Exemplo |
|---|---|---|
| Arquivo | `snake_case.py` | `bolao_service.py` |
| Classe | `PascalCase` | `BolaoPredicition` |
| Função | `snake_case` | `settle_predictions` |
| Constante | `UPPER_SNAKE` | `POINTS_EXACT_SCORE = 10` |
| Schema Request | `[Ação]Request` | `CreatePredictionRequest` |
| Schema Response | `[Entidade]Response` | `PredictionResponse` |
| Exceção de domínio | `[Motivo]Error` | `BettingClosedError` |
| Router prefix | `/kebab-case` | `/venue-map` |
| Celery task | `snake_case_verb` | `settle_bolao_predictions` |
| Cache key | `dominio:entidade:param` | `bolao:ranking:50:0` |

---

*Última atualização: 2026-05-21 | Parte integrante do guia principal em `../../CLAUDE.md`*
