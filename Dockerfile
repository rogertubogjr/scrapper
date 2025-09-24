# Use Playwright's official Python image with browsers preinstalled
# Match the version in requirements.txt (playwright==1.55.0)
FROM mcr.microsoft.com/playwright/python:v1.55.0-noble

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install minimal build tools for packages needing compilation (e.g., madoka)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       python3-dev \
       musl-dev \
       libpq-dev \
       gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (better layer caching)
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Copy the rest of the application
COPY . /app

# Expose Flask port
EXPOSE 5001

# Playwright base image includes browsers already
# Set a larger shared memory to avoid Chromium crashes (also configurable via compose)

# Default command
CMD ["python", "run.py"]
