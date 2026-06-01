FROM python:3.12-slim

WORKDIR /app

# System dependencies (removed heavy OCR dependencies for Legal AI)
RUN apt-get update && apt-get install -y \
    build-essential \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
RUN pip install uv==0.5.15

# Copy requirements and install
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt --no-cache

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Default command
CMD ["sh", "-c", "alembic upgrade head && uvicorn api.main:app --host 0.0.0.0 --port 8000"]
