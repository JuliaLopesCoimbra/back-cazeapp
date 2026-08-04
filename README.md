# Casa CazéTV Copa 2026 — Backend

API em FastAPI (Python) com Postgres (Railway), Redis, Celery e serviços auxiliares (roulette, photo-ai).

## Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e **aberto** (o ícone da baleia precisa estar rodando antes de qualquer comando `docker`)
- Acesso ao projeto no [Railway](https://railway.app) (banco Postgres)

## 1. Clonar e configurar

```bash
git clone <url-do-repo> back
cd back
cp .env.example .env
```

Edite o `.env` e preencha pelo menos:

- `AUTH_DATABASE_URL`, `ADMIN_DATABASE_URL`, `INTERACTION_DATABASE_URL`, `ROULETTE_DATABASE_URL`, `NOTIFICATIONS_DATABASE_URL` — todas apontam para a **mesma** instância Postgres do Railway. Use a URL **pública** (host `*.proxy.rlwy.net`), nunca a `*.railway.internal` (essa só funciona dentro da rede do Railway, não do seu PC).
  - Onde achar: Railway → serviço Postgres → **Settings → Networking → TCP Proxy** (gere se não existir) → aba **Variables** → `DATABASE_PUBLIC_URL`.
- `JWT_SECRET`, `JWT_REFRESH_SECRET` — qualquer string aleatória em dev.
- Os demais (AWS, SMTP, OAuth) só são necessários se for testar essas features específicas (upload de foto, envio de e-mail, login social). Sem eles a API sobe normalmente, só essas rotas específicas falham.

## 2. Rodar (modo simples — recomendado para desenvolvimento)

Só a API, sem Redis/nginx/Traefik/Celery. Ideal para desenvolver rotas e testar no Postman/frontend.

```bash
docker compose -f docker-compose.dev.yml up -d --build
```

- API disponível em **http://localhost:8000**
- Hot-reload ativado — qualquer alteração em `app/` reinicia o servidor automaticamente
- Health check: `curl http://localhost:8000/health`

Comandos úteis:

```bash
docker compose -f docker-compose.dev.yml logs -f api    # ver logs em tempo real
docker compose -f docker-compose.dev.yml restart api    # reiniciar (não recarrega .env!)
docker compose -f docker-compose.dev.yml up -d --force-recreate  # recarregar após mudar .env
docker compose -f docker-compose.dev.yml down            # parar e remover
```

> Sem Redis, o cache e o rate-limiting ficam desativados automaticamente (o app detecta e loga um aviso, não trava) — ver `app/infra/redis.py`.

## 3. Rodar (stack completo — nginx + Traefik + Redis + Celery)

Espelha a topologia de produção (múltiplos serviços, load balancer, workers de background). Use se for testar notificações, tarefas assíncronas ou o comportamento de produção.

```bash
docker compose up -d --build
```

Serviços expostos:

| Serviço | Porta host | Descrição |
|---|---|---|
| API (via Traefik) | `8000` | Roteamento principal |
| Dashboard Traefik | `8080` | `http://localhost:8080/dashboard/` |
| nginx (TLS) | `8081` / `8443` | HTTP / HTTPS |
| Redis | `6380` | Próprio deste projeto (`back-redis`) |

> As portas 80/443/6379 padrão não são usadas de propósito — este projeto pode coexistir na mesma máquina com outros projetos Docker sem conflito de nome/porta.

```bash
docker compose down   # parar tudo
```

## Solução de problemas comuns

- **`docker compose up` falha com erro de pipe/`dockerDesktopLinuxEngine`**: Docker Desktop ainda está iniciando. Espere alguns segundos e tente de novo.
- **`Conflict. The container name "/xxx" is already in use`**: outro projeto Docker na sua máquina já usa esse nome de container. Rode `docker ps -a` para identificar e ajuste o `container_name` em `docker-compose.yml` se necessário.
- **`Bind for 0.0.0.0:PORTA failed: port is already allocated`**: outra aplicação (ou outro projeto Docker) já está usando essa porta no host. Rode `docker ps` para ver quem está usando e mude a porta no `docker-compose*.yml`.
- **`could not translate host name "postgres.railway.internal"`**: seu `.env` está com a URL interna do Railway. Troque pela URL pública (`*.proxy.rlwy.net`) — veja o passo 1.
- **Editou o `.env` e nada mudou**: `docker compose restart` não relê o `.env`. Use `up -d --force-recreate` (ou `--build` se também mudou código/dependências).
