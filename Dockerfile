FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DM_DATA_DIR=/app/data \
    DM_TRANSPORT=http \
    DM_HOST=0.0.0.0 \
    DM_PORT=8000 \
    DM_ENVIRONMENT=production

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

RUN addgroup --system --gid 10001 app \
    && adduser --system --uid 10001 --ingroup app app \
    && mkdir -p /app/data \
    && chown -R app:app /app/data

VOLUME ["/app/data"]
EXPOSE 8000
USER app
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)"
CMD ["dis-mevzuat", "serve"]
