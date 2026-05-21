"""
Tradução PT-BR dos dados retornados pela API-Sports.
Aplicado antes de cachear — frontend recebe tudo em português.
"""

# ─── Times ────────────────────────────────────────────────────────────────────

TEAMS: dict[str, str] = {
    "Brazil": "Brasil",
    "France": "França",
    "Germany": "Alemanha",
    "Spain": "Espanha",
    "Portugal": "Portugal",
    "Netherlands": "Países Baixos",
    "Belgium": "Bélgica",
    "England": "Inglaterra",
    "Italy": "Itália",
    "Croatia": "Croácia",
    "Morocco": "Marrocos",
    "Senegal": "Senegal",
    "Japan": "Japão",
    "South Korea": "Coreia do Sul",
    "Australia": "Austrália",
    "Switzerland": "Suíça",
    "USA": "Estados Unidos",
    "United States": "Estados Unidos",
    "Mexico": "México",
    "Ecuador": "Equador",
    "Uruguay": "Uruguai",
    "Colombia": "Colômbia",
    "Chile": "Chile",
    "Peru": "Peru",
    "Bolivia": "Bolívia",
    "Paraguay": "Paraguai",
    "Venezuela": "Venezuela",
    "Canada": "Canadá",
    "Costa Rica": "Costa Rica",
    "Honduras": "Honduras",
    "Panama": "Panamá",
    "Jamaica": "Jamaica",
    "Trinidad and Tobago": "Trinidad e Tobago",
    "Saudi Arabia": "Arábia Saudita",
    "Iran": "Irã",
    "Qatar": "Catar",
    "New Zealand": "Nova Zelândia",
    "Ghana": "Gana",
    "Cameroon": "Camarões",
    "Nigeria": "Nigéria",
    "Tunisia": "Tunísia",
    "Egypt": "Egito",
    "Algeria": "Argélia",
    "Ivory Coast": "Costa do Marfim",
    "Senegal": "Senegal",
    "Scotland": "Escócia",
    "Wales": "Gales",
    "Denmark": "Dinamarca",
    "Poland": "Polônia",
    "Serbia": "Sérvia",
    "Czech Republic": "República Tcheca",
    "Czechia": "República Tcheca",
    "Slovakia": "Eslováquia",
    "Hungary": "Hungria",
    "Romania": "Romênia",
    "Greece": "Grécia",
    "Turkey": "Turquia",
    "Ukraine": "Ucrânia",
    "Russia": "Rússia",
    "Sweden": "Suécia",
    "Norway": "Noruega",
    "Finland": "Finlândia",
    "Austria": "Áustria",
    "Albania": "Albânia",
    "Iceland": "Islândia",
    "Ireland": "Irlanda",
    "North Macedonia": "Macedônia do Norte",
    "Slovenia": "Eslovênia",
    "Bosnia": "Bósnia e Herzegovina",
    "Bosnia and Herzegovina": "Bósnia e Herzegovina",
    "China": "China",
    "India": "Índia",
    "Thailand": "Tailândia",
    "Vietnam": "Vietnã",
    "Indonesia": "Indonésia",
    "Philippines": "Filipinas",
    "Iraq": "Iraque",
    "Syria": "Síria",
    "Jordan": "Jordânia",
    "Oman": "Omã",
    "United Arab Emirates": "Emirados Árabes Unidos",
    "South Africa": "África do Sul",
    "Cameroon": "Camarões",
    "Mali": "Mali",
    "Haiti": "Haiti",
}

# ─── Fase / rodada ────────────────────────────────────────────────────────────

ROUNDS: dict[str, str] = {
    "Group Stage - 1": "Fase de Grupos",
    "Group Stage - 2": "Fase de Grupos",
    "Group Stage - 3": "Fase de Grupos",
    "Round of 32": "16 avos de Final",
    "Round of 16": "Oitavas de Final",
    "Quarter-finals": "Quartas de Final",
    "Semi-finals": "Semifinais",
    "3rd Place Final": "Disputa do 3º Lugar",
    "Final": "Final",
}

# ─── Status do jogo ───────────────────────────────────────────────────────────

STATUS_LONG: dict[str, str] = {
    "Not Started": "Não iniciado",
    "First Half": "1º Tempo",
    "Halftime": "Intervalo",
    "Second Half": "2º Tempo",
    "Extra Time": "Prorrogação",
    "Break Time": "Intervalo da Prorrogação",
    "Penalty In Progress": "Pênaltis",
    "Match Finished": "Encerrado",
    "Match Finished After Extra Time": "Encerrado (Prorrogação)",
    "Match Finished After Penalty": "Encerrado (Pênaltis)",
    "Time to be Defined": "A definir",
    "Match Postponed": "Adiado",
    "Match Cancelled": "Cancelado",
    "Match Abandoned": "Abandonado",
    "Technical Loss": "Derrota técnica",
    "WalkOver": "W.O.",
    "In Progress": "Em andamento",
    "Match Suspended": "Suspenso",
    "Match Interrupted": "Interrompido",
}

# ─── Tipos e detalhes de eventos ──────────────────────────────────────────────

EVENT_TYPES: dict[str, str] = {
    "Goal": "Gol",
    "Card": "Cartão",
    "subst": "Substituição",
    "Var": "VAR",
}

EVENT_DETAILS: dict[str, str] = {
    # Gols
    "Normal Goal": "Gol",
    "Own Goal": "Gol Contra",
    "Penalty": "Pênalti",
    "Missed Penalty": "Pênalti Perdido",
    # Cartões
    "Yellow Card": "Cartão Amarelo",
    "Red Card": "Cartão Vermelho",
    "Yellow Red Card": "Segundo Amarelo (Expulsão)",
    # Substituições
    "Substitution 1": "Substituição",
    "Substitution 2": "Substituição",
    "Substitution 3": "Substituição",
    "Substitution 4": "Substituição",
    "Substitution 5": "Substituição",
    "Substitution 6": "Substituição",
    # VAR
    "Goal confirmed": "Gol confirmado pelo VAR",
    "Goal cancelled": "Gol anulado pelo VAR",
    "Card upgrade": "Cartão revisado pelo VAR",
    "Card cancelled": "Cartão anulado pelo VAR",
    "Penalty confirmed": "Pênalti confirmado pelo VAR",
    "Penalty cancelled": "Pênalti anulado pelo VAR",
}

# ─── Funções de tradução ──────────────────────────────────────────────────────

def _t(mapping: dict[str, str], value: str) -> str:
    return mapping.get(value, value)


def translate_team(team: dict) -> dict:
    if not team:
        return team
    return {**team, "name": _t(TEAMS, team.get("name", ""))}


def translate_fixture(fixture: dict) -> dict:
    """Traduz um objeto fixture completo para PT-BR."""
    if not fixture:
        return fixture

    f = dict(fixture)

    # Teams
    if "teams" in f:
        f["teams"] = {
            "home": translate_team(f["teams"].get("home", {})),
            "away": translate_team(f["teams"].get("away", {})),
        }

    # League round
    if "league" in f:
        league = dict(f["league"])
        league["round"] = _t(ROUNDS, league.get("round", ""))
        f["league"] = league

    # Status
    if "fixture" in f:
        fix = dict(f["fixture"])
        if "status" in fix:
            status = dict(fix["status"])
            status["long"] = _t(STATUS_LONG, status.get("long", ""))
            fix["status"] = status
        f["fixture"] = fix

    return f


def translate_event(event: dict) -> dict:
    """Traduz um evento (gol, cartão, sub) para PT-BR."""
    if not event:
        return event

    e = dict(event)

    if "team" in e:
        e["team"] = translate_team(e["team"])

    if "type" in e:
        e["type"] = _t(EVENT_TYPES, e["type"])

    if "detail" in e:
        e["detail"] = _t(EVENT_DETAILS, e["detail"])

    return e


def translate_fixtures(fixtures: list) -> list:
    return [translate_fixture(f) for f in fixtures]


def translate_events(events: list) -> list:
    return [translate_event(e) for e in events]


def translate_standings(standings: list) -> list:
    """Traduz os nomes dos times nas standings."""
    result = []
    for league_entry in standings:
        entry = dict(league_entry)
        if "league" in entry:
            league = dict(entry["league"])
            if "standings" in league:
                translated_groups = []
                for group in league["standings"]:
                    translated_group = []
                    for team_entry in group:
                        te = dict(team_entry)
                        if "team" in te:
                            te["team"] = translate_team(te["team"])
                        if "group" in te:
                            # Ex: "Group A" → "Grupo A"
                            te["group"] = te["group"].replace("Group ", "Grupo ")
                        translated_group.append(te)
                    translated_groups.append(translated_group)
                league["standings"] = translated_groups
            entry["league"] = league
        result.append(entry)
    return result
