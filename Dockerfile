FROM python:3.11-slim

WORKDIR /app

# Install git and system deps
RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"
ENV POETRY_VIRTUALENVS_CREATE=false

# Copy deps
COPY pyproject.toml poetry.lock* ./

# Install deps
RUN poetry install --no-interaction --no-ansi --no-root

# Copy code
COPY . .

# Install project
RUN poetry install --no-interaction --no-ansi

EXPOSE 8000
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
