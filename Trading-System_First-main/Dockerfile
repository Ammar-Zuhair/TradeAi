# Use Python 3.9 on Debian (Linux) - Much smaller and faster
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies (if needed)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project files
COPY . .

# Create directories for persistent data
RUN mkdir -p logs data

# Health check
HEALTHCHECK --interval=5m --timeout=3s \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Set the entry point
CMD ["python", "Run_System_Dual.py"]
