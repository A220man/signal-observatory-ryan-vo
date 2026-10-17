FROM python:3.12-slim AS base

WORKDIR /app

RUN adduser --disabled-password --gecos "" --home /home/appuser appuser

FROM base AS dependencies

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS runtime

COPY --from=dependencies /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

COPY backend/app ./app
COPY backend/pyproject.toml .

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]