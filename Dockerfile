# Lightweight Python image
FROM python:3.11-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create app user and directory
RUN useradd --create-home appuser
WORKDIR /app

# Install system deps (postgres client libraries if using psycopg2-binary you can skip libpq-dev)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better cache
# Put your project's Python dependencies in requirements.txt at repo root
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY . /app

# Ensure correct permissions
RUN chown -R appuser:appuser /app
USER appuser

# Expose port and define default command
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]