FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DM_DATA_DIR=/app/data \
    DM_TRANSPORT=http \
    DM_HOST=0.0.0.0 \
    DM_PORT=8000

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

VOLUME ["/app/data"]
EXPOSE 8000
CMD ["dis-mevzuat", "serve"]
