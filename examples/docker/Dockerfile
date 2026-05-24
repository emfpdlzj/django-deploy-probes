FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings
ENV APP_VERSION=0.1.0
ENV GIT_COMMIT=local
ENV GIT_BRANCH=main
ENV BUILD_TIME=2026-05-17T00:00:00+09:00
ENV DEPLOY_SLOT=blue

WORKDIR /src

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY django_deploy_probes ./django_deploy_probes
RUN pip install --no-cache-dir . gunicorn

WORKDIR /app

COPY examples/docker .
RUN python manage.py migrate --noinput

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --retries=3 CMD curl --fail http://127.0.0.1:8000/healthz || exit 1

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
