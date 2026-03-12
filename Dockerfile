FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 5070

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5070", "--root-path", "/ppi"]
