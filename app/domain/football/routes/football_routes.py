import copy
from fastapi import APIRouter, Depends, Query, HTTPException
from app.core.security.auth_dependency import get_current_user
from app.infra.redis import redis_client, CacheKeys
from app.domain.football.services.football_service import (
    get_brazil_fixtures,
    get_brazil_live,
    get_fixture_events,
    get_wc_standings,
    get_brazil_stats,
    debug_api,
    _fetch_raw,
)
from app.domain.football.translations import translate_fixture

router = APIRouter(prefix="/football", tags=["football"])


@router.get("/brazil/fixtures")
def brazil_fixtures(current_user=Depends(get_current_user)):
    """Todos os jogos do Brasil na Copa do Mundo 2026."""
    return get_brazil_fixtures()


@router.get("/brazil/live")
def brazil_live(current_user=Depends(get_current_user)):
    """Jogo ao vivo do Brasil. Retorna lista vazia se não estiver jogando."""
    return get_brazil_live()


@router.get("/fixtures/{fixture_id}/events")
def fixture_events(fixture_id: int, current_user=Depends(get_current_user)):
    """Gols, cartões e substituições de uma partida."""
    return get_fixture_events(fixture_id)


@router.get("/standings")
def wc_standings(current_user=Depends(get_current_user)):
    """Classificação dos grupos da Copa do Mundo 2026."""
    return get_wc_standings()


@router.get("/brazil/stats")
def brazil_stats():
    """Jogos, vitórias, gols e grupo do Brasil. Público — usado no header da página /games."""
    return get_brazil_stats()


# ─── Debug / Diagnóstico ──────────────────────────────────────────────────────

@router.get("/debug/raw")
def debug_raw(
    path: str = Query(default="/fixtures", description="Ex: /fixtures, /standings, /leagues"),
    league: int = Query(default=1),
    season: int = Query(default=2022),
    team: int = Query(default=6),
    current_user=Depends(get_current_user),
):
    """Retorna a resposta bruta da API-Sports sem cache. Use para diagnóstico."""
    params = {"league": league, "season": season, "team": team}
    return debug_api(path, params)


@router.get("/debug/live-now")
def live_now(current_user=Depends(get_current_user)):
    """Lista todos os jogos ao vivo agora em qualquer liga (para testes)."""
    raw = _fetch_raw("/fixtures", {"live": "all"})
    return [
        {
            "id": f["fixture"]["id"],
            "league": f["league"]["name"],
            "home": f["teams"]["home"]["name"],
            "away": f["teams"]["away"]["name"],
            "home_goals": f["goals"]["home"],
            "away_goals": f["goals"]["away"],
            "elapsed": f["fixture"]["status"]["elapsed"],
            "status": f["fixture"]["status"]["short"],
        }
        for f in raw.get("response", [])
    ]


@router.post("/debug/mock-live")
def mock_live(
    elapsed: int = Query(default=32, description="Minuto do jogo simulado"),
    home_goals: int = Query(default=1),
    away_goals: int = Query(default=0),
    fixture_id: int | None = Query(default=None, description="ID real da API-Sports. Se informado, usa dados reais."),
    current_user=Depends(get_current_user),
):
    """Injeta um fixture ao vivo no cache Redis. Se fixture_id informado, busca dados reais da API-Sports."""
    if fixture_id is not None:
        raw = _fetch_raw("/fixtures", {"id": fixture_id})
        fixtures = raw.get("response", [])
        if not fixtures:
            raise HTTPException(status_code=404, detail=f"Fixture {fixture_id} não encontrado na API-Sports.")
        fixture_data = translate_fixture(fixtures[0])
        redis_client.set(CacheKeys.football_brazil_live(), [fixture_data], ttl=600)
        home = fixture_data["teams"]["home"]["name"]
        away = fixture_data["teams"]["away"]["name"]
        return {"ok": True, "fixture_id": fixture_id, "partida": f"{home} x {away}"}

    mock = {
        "fixture": {
            "id": 855744,
            "date": "2022-11-24T16:00:00+00:00",
            "status": {"long": "1º Tempo", "short": "1H", "elapsed": elapsed},
            "venue": {"name": "Lusail Stadium", "city": "Lusail"},
        },
        "league": {"round": "Fase de Grupos", "season": 2022},
        "teams": {
            "home": {
                "id": 6,
                "name": "Brasil",
                "logo": "https://media.api-sports.io/football/teams/6.png",
                "winner": None,
            },
            "away": {
                "id": 9,
                "name": "Sérvia",
                "logo": "https://media.api-sports.io/football/teams/9.png",
                "winner": None,
            },
        },
        "goals": {"home": home_goals, "away": away_goals},
        "score": {
            "halftime": {"home": None, "away": None},
            "fulltime": {"home": None, "away": None},
            "extratime": {"home": None, "away": None},
            "penalty": {"home": None, "away": None},
        },
    }
    redis_client.set(CacheKeys.football_brazil_live(), [mock], ttl=600)
    return {
        "ok": True,
        "partida": f"Brasil {home_goals} x {away_goals} Sérvia",
        "minuto": elapsed,
        "dica": "Para remover, DELETE /football/debug/mock-live",
    }


@router.delete("/debug/mock-live")
def clear_mock_live(current_user=Depends(get_current_user)):
    """Remove o mock de jogo ao vivo do cache."""
    redis_client.delete(CacheKeys.football_brazil_live())
    return {"ok": True, "msg": "Mock removido. Próxima chamada buscará da API real."}


@router.delete("/cache/clear")
def clear_football_cache(current_user=Depends(get_current_user)):
    """Limpa o cache Redis de todos os endpoints de football."""
    keys = [
        CacheKeys.football_brazil_fixtures(),
        CacheKeys.football_brazil_live(),
        CacheKeys.football_standings(),
        "football:brazil:stats",
    ]
    deleted = redis_client.delete(*keys)
    return {"cleared": deleted, "keys": keys}
