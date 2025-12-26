FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# Install Poetry (so we can install deps without packaging the project)
RUN pip install --upgrade pip && pip install "poetry>=1.6"

# Copy only dependency files first (better caching)
COPY pyproject.toml poetry.lock* /app/

# Install dependencies only (do NOT build/install the project package)
RUN poetry install --no-root

# Copy the application code
COPY . /app

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]