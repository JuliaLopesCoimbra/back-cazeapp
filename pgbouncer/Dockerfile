FROM alpine:3.19

RUN apk add --no-cache pgbouncer gettext netcat-openbsd

# Cria o usuário pgbouncer antes de usar no chown
RUN addgroup -S pgbouncer && adduser -S -G pgbouncer pgbouncer

RUN mkdir -p /etc/pgbouncer /var/log/pgbouncer /var/run/pgbouncer && \
    chown -R pgbouncer:pgbouncer /etc/pgbouncer /var/log/pgbouncer /var/run/pgbouncer

COPY --chown=pgbouncer:pgbouncer pgbouncer.ini.template /etc/pgbouncer/pgbouncer.ini.template
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER pgbouncer

EXPOSE 6432

ENTRYPOINT ["/entrypoint.sh"]
