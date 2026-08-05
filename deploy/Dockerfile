FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY deploy/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY curso_mcp ./curso_mcp
COPY deploy/main.py ./main.py

# Cloud Run fija el puerto por entorno; 8080 es solo el valor por defecto local.
ENV PORT=8080
EXPOSE 8080

CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}
