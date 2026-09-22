FROM python:3.11-slim

# The engine uses the Docker CLI to create isolated, short-lived runner
# containers. The runners themselves remain non-root and capability-free.
RUN apt-get update \
    && apt-get install -y --no-install-recommends docker.io docker-cli \
    && docker --version \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
