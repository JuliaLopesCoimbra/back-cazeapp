import logging
import httpx
from app.config.settings import settings
from app.infra.redis import redis_client, CacheKeys
from app.domain.football.translations import (
    translate_fixtures,
    translate_events,
    translate_standings,
)

logger = logging.getLogger(__name__)

_BASE_URL = "https://v3.football.api-sports.io"
_WC_LEAGUE_ID = 1      # FIFA World Cup
_BRAZIL_TEAM_ID = 6

def _wc_season() -> int:
    return settings.APISPORTS_WC_SEASON


def _headers() -> dict:
    return {"x-apisports-key": settings.APISPORTS_KEY or ""}


def _fetch_raw(path: str, params: dict) -> dict:
    """Chama a API-Sports e retorna o JSON completo (para debug e lógica de erro)."""
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{_BASE_URL}{path}", params=params, headers=_headers())
            data = resp.json()
            # Loga a resposta completa para facilitar debug
            logger.info(
                "API-Sports %s | status=%s | results=%s | errors=%s",
                path,
                resp.status_code,
                data.get("results"),
                data.get("errors"),
            )
            return data
    except Exception as exc:
        logger.error("Erro HTTP API-Sports %s: %s", path, exc)
        return {"response": [], "errors": str(exc)}


def _fetch(path: str, params: dict, cache_key: str, ttl: int) -> list:
    """
    Chama a API-Sports com cache Redis.
    Só armazena em cache se a resposta tiver dados (evita cachear erros).
    """
    cached = redis_client.get(cache_key)
    if cached is not None:
        return cached

    raw = _fetch_raw(path, params)
    result = raw.get("response", [])
    errors = raw.get("errors", {})

    if errors:
        logger.warning("API-Sports retornou erros em %s: %s", path, errors)

    # Não armazena em cache se veio vazio E houver erros (pode ser problema de chave/quota)
    if result or not errors:
        redis_client.set(cache_key, result, ttl=ttl)

    return result


# ─── Debug (retorna resposta bruta sem cache) ─────────────────────────────────

def debug_api(path: str, params: dict) -> dict:
    """Retorna a resposta bruta da API-Sports. Use apenas para diagnóstico."""
    raw = _fetch_raw(path, params)
    raw["_key_loaded"] = bool(settings.APISPORTS_KEY)
    raw["_key_prefix"] = (settings.APISPORTS_KEY or "")[:6] + "..." if settings.APISPORTS_KEY else "VAZIA"
    return raw


# ─── Fixtures do Brasil ───────────────────────────────────────────────────────

def get_brazil_fixtures() -> list:
    """Todos os jogos do Brasil na Copa. Cache 24h (dados históricos não mudam)."""
    key = CacheKeys.football_brazil_fixtures()
    cached = redis_client.get(key)
    if cached is not None:
        return cached

    raw = _fetch_raw("/fixtures", {"league": _WC_LEAGUE_ID, "season": _wc_season(), "team": _BRAZIL_TEAM_ID})
    errors = raw.get("errors")
    result = translate_fixtures(raw.get("response", []))

    if result:
        # Dados ok — cache 24h (Copa encerrada, nunca muda)
        redis_client.set(key, result, ttl=86400)
    elif errors:
        # API falhou — cache vazio por 60s para não martelelar o rate limit
        redis_client.set(key, [], ttl=60)

    return result


# ─── Jogo ao vivo do Brasil ───────────────────────────────────────────────────

def get_brazil_live() -> list:
    """Jogo ao vivo do Brasil — lista vazia se não estiver jogando (cache 30s, PT-BR)."""
    key = CacheKeys.football_brazil_live()
    cached = redis_client.get(key)
    if cached is not None:
        return cached

    raw = _fetch_raw("/fixtures", {"live": "all", "league": _WC_LEAGUE_ID, "team": _BRAZIL_TEAM_ID})
    result = translate_fixtures(raw.get("response", []))
    redis_client.set(key, result, ttl=30)
    return result


# ─── Eventos de uma partida ───────────────────────────────────────────────────

def get_fixture_events(fixture_id: int) -> list:
    """Gols, cartões e substituições. Cache 30s se ao vivo, 1h se encerrado. PT-BR."""
    key = CacheKeys.football_fixture_events(fixture_id)
    cached = redis_client.get(key)
    if cached is not None:
        return cached

    live = get_brazil_live()
    live_ids = {f["fixture"]["id"] for f in live if "fixture" in f}
    ttl = 30 if fixture_id in live_ids else 3600

    raw = _fetch_raw("/fixtures/events", {"fixture": fixture_id})
    result = translate_events(raw.get("response", []))
    if result or not raw.get("errors"):
        redis_client.set(key, result, ttl=ttl)
    return result


# ─── Stats do Brasil (para o header da página de jogos) ──────────────────────

def get_brazil_stats() -> dict:
    """
    Retorna jogos, vitórias, gols e grupo do Brasil em TODAS as fases.
    - jogos/vitórias/gols: contados via fixtures (todas as fases)
    - grupo/pontos: extraídos do standings (fase de grupos)
    Cache 1h.
    """
    key = "football:brazil:stats"
    cached = redis_client.get(key)
    if cached is not None:
        return cached

    default = {"jogos": 0, "vitorias": 0, "empates": 0, "gols": 0, "grupo": "—", "pontos": 0}

    # ── Grupo e pontos: vem do standings (só tem fase de grupos) ──────────────
    grupo_letra = "—"
    pontos = 0
    raw_st = _fetch_raw("/standings", {"league": _WC_LEAGUE_ID, "season": _wc_season()})
    for league_entry in raw_st.get("response", []):
        for group in league_entry.get("league", {}).get("standings", []):
            for team_entry in group:
                if team_entry.get("team", {}).get("id") == _BRAZIL_TEAM_ID:
                    group_raw = team_entry.get("group", "Grupo ?")
                    grupo_letra = group_raw.replace("Group ", "").replace("Grupo ", "").strip()
                    pontos = team_entry.get("points", 0)

    # ── jogos/vitórias/gols: contados em todos os fixtures encerrados ─────────
    FINISHED = {"FT", "AET", "PEN"}
    raw_fx = _fetch_raw("/fixtures", {"league": _WC_LEAGUE_ID, "season": _wc_season(), "team": _BRAZIL_TEAM_ID})

    jogos = vitorias = empates = gols = 0
    for f in raw_fx.get("response", []):
        if f.get("fixture", {}).get("status", {}).get("short") not in FINISHED:
            continue
        jogos += 1
        home = f.get("teams", {}).get("home", {})
        away = f.get("teams", {}).get("away", {})
        goals = f.get("goals", {})

        if home.get("id") == _BRAZIL_TEAM_ID:
            gols += goals.get("home") or 0
            if home.get("winner") is True:
                vitorias += 1
            elif home.get("winner") is None:
                empates += 1
        else:
            gols += goals.get("away") or 0
            if away.get("winner") is True:
                vitorias += 1
            elif away.get("winner") is None:
                empates += 1

    result = {
        "jogos":    jogos,
        "vitorias": vitorias,
        "empates":  empates,
        "gols":     gols,
        "grupo":    grupo_letra,
        "pontos":   pontos,
    }
    redis_client.set(key, result, ttl=3600)
    return result


# ─── Classificação dos grupos ─────────────────────────────────────────────────

def get_wc_standings() -> list:
    """Classificação de todos os grupos (cache 1 h, PT-BR)."""
    key = CacheKeys.football_standings()
    cached = redis_client.get(key)
    if cached is not None:
        return cached

    raw = _fetch_raw("/standings", {"league": _WC_LEAGUE_ID, "season": _wc_season()})
    result = translate_standings(raw.get("response", []))
    if result:
        redis_client.set(key, result, ttl=86400)
    elif raw.get("errors"):
        redis_client.set(key, [], ttl=60)
    return result
