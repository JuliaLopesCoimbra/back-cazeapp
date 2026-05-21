"""Configuração do Celery para processamento assíncrono de tarefas"""
from celery import Celery
from celery.schedules import crontab
from app.config.settings import settings

# IMPORTANTE: Importar todos os modelos necessários ANTES de criar a instância do Celery
# Isso garante que o SQLAlchemy possa configurar corretamente os relacionamentos
# quando as tasks forem executadas no worker
from app.domain.admin.models.news_model import NewsPost  # noqa: F401
from app.domain.admin.models.event_model import Event  # noqa: F401
from app.domain.admin.models.news_image_model import NewsImage  # noqa: F401
from app.domain.admin.models.ad_view_model import AdView  # noqa: F401
from app.domain.auth.models.user_model import User  # noqa: F401
from app.domain.users.models.comment_model import Comment  # noqa: F401
from app.domain.users.models.comment_like_model import CommentLike  # noqa: F401
from app.domain.photo_ai.models.user_face_model import UserFace  # noqa: F401
from app.domain.users.models.user_photo_model import UserPhoto  # noqa: F401

# Construir URL do Redis para Celery
if settings.REDIS_URL:
    broker_url = settings.REDIS_URL
    backend_url = settings.REDIS_URL
else:
    password_part = f":{settings.REDIS_PASSWORD}@" if settings.REDIS_PASSWORD else ""
    broker_url = f"redis://{password_part}{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
    backend_url = f"redis://{password_part}{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB + 1}"  # DB diferente para resultados

# Criar instância do Celery
celery_app = Celery(
    'notifications',
    broker=broker_url,
    backend=backend_url,
    include=[
        'app.domain.users.tasks.notification_tasks',
        'app.domain.users.tasks.push_tasks',  # Worker de notificação para o navegador (Web Push)
        'app.domain.admin.tasks.ad_view_tasks',  # Tasks para processar views de anúncios
        'app.domain.analytics.tasks.cleanup_tasks',  # Limpeza periódica de dados de analytics
        'app.domain.photo_ai.tasks.face_matching_tasks',  # Vinculação automática de fotos para torcida
    ]
)

# Configurações do Celery
celery_app.conf.update(
    # Serialização
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone
    timezone='UTC',
    enable_utc=True,
    
    # Timeouts
    task_time_limit=30 * 60,  # 30 minutos máximo
    task_soft_time_limit=25 * 60,  # 25 minutos soft limit
    
    # Workers
    worker_prefetch_multiplier=4,  # Processar 4 tarefas por vez por worker
    worker_max_tasks_per_child=1000,  # Reiniciar worker após 1000 tarefas (evitar memory leaks)
    
    # Retry
    task_acks_late=True,  # Só marca como completa após processar
    task_reject_on_worker_lost=True,  # Rejeita se worker morrer
    
    # Result backend
    result_expires=3600,  # Resultados expiram em 1 hora
    
    # Task tracking
    task_track_started=True,
    
    # Broker connection retry (evita warnings)
    broker_connection_retry_on_startup=True,

    # Roteamento de filas: cada worker consome apenas sua fila dedicada
    task_routes={
        'notifications.*': {'queue': 'notifications'},
        'ads.*': {'queue': 'ads'},
        'analytics.*': {'queue': 'celery'},
        'photo_ai.*': {'queue': 'celery'},
    },

    # Tarefas agendadas (Celery Beat)
    beat_schedule={
        "cleanup-page-views-daily": {
            "task": "analytics.cleanup_page_views",
            "schedule": crontab(hour=3, minute=0),  # 03:00 UTC todos os dias
        },
    },
)

# IMPORTANTE: Importar explicitamente todas as tasks para garantir que sejam registradas
# Isso é necessário para que o worker reconheça todas as tasks, especialmente após adicionar novas
from app.domain.users.tasks import notification_tasks  # noqa: F401
from app.domain.users.tasks import push_tasks  # noqa: F401
from app.domain.admin.tasks import ad_view_tasks  # noqa: F401
from app.domain.analytics.tasks import cleanup_tasks  # noqa: F401
from app.domain.photo_ai.tasks import face_matching_tasks  # noqa: F401

