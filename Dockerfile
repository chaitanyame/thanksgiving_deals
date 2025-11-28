# Dockerfile for Slickdeals scraper
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY scripts/requirements.txt /app/scripts/
RUN pip install --no-cache-dir -r scripts/requirements.txt

# Copy all project files
COPY . /app/

# Create data directory
RUN mkdir -p /app/data

# Run the scraper script
CMD ["python", "scripts/sync_deals.py"]
