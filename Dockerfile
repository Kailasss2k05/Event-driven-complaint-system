FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY requirements.txt ./
RUN pip install --no-cache-dir --retries 5 --timeout 300 -r requirements.txt

COPY . ./

CMD ["uvicorn", "backend.complaint_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
