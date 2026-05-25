"""
Celery tasks para liquidação automática do bolão.

Para ativar: importar e registrar estas tasks no celery_app da aplicação.
Exemplo de execução: celery -A app.celery_app worker --beat
"""
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def settle_finished_matches():
    """
    Verifica jogos finalizados via API-Sports e liquida as apostas pendentes.
    Deve ser chamada periodicamente (ex.: a cada 5 minutos via beat schedule).
    """
    from app.config.roulette_db import SessionLocal
    from app.domain.football.services.football_service import get_brazil_fixtures
    from app.domain.bolao.services.bolao_service import settle_predictions

    db = SessionLocal()
    try:
        fixtures = get_brazil_fixtures()
        finished = [
            f for f in fixtures
            if f["fixture"]["status"]["short"] in ("FT", "AET", "PEN")
        ]

        total_settled = 0
        for f in finished:
            fixture_id = f["fixture"]["id"]
            actual_home = f["goals"]["home"]
            actual_away = f["goals"]["away"]

            if actual_home is None or actual_away is None:
                continue

            count = settle_predictions(db, fixture_id, actual_home, actual_away)
            if count:
                logger.info(
                    "Liquidadas %d apostas para o jogo %d (%s x %s: %d-%d)",
                    count, fixture_id,
                    f["teams"]["home"]["name"], f["teams"]["away"]["name"],
                    actual_home, actual_away,
                )
            total_settled += count

        return total_settled

    except Exception as exc:
        logger.error("Erro ao liquidar apostas: %s", exc, exc_info=True)
        raise
    finally:
        db.close()
