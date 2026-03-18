FROM python:3.14-slim AS base


ENV APP_DATA_DIR=/var/lib/app-data \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"
    
RUN mkdir -p $APP_DATA_DIR


FROM base AS builder

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN pip install --no-cache-dir poetry==2.0.0 && \
    poetry config virtualenvs.in-project true && \
    poetry install --no-root --only main --no-interaction --no-ansi

FROM base as runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 

ENV DB_DSN=sqlite+aiosqlite:///${APP_DATA_DIR}/app_storage.db \
    LEMMAS_CACHE_MAXSIZE=1000 \
    SAVE_BUTCH_SIZE=200 \
    WRITER_CHUNK_SIZE_KB=8 \
    UPLOAD_CHUNK_SIZE_MB=2 \
    MAX_UPLOADING_USERS=10 \
    MAX_WORKERS=4 \
    WORKERS_TYPE='processes'

WORKDIR /app
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY app ./app


