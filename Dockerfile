# Intent Orchestration Platform - Main Application Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for frontend build
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy backend code
COPY backend/ ./backend/
COPY demo/ ./demo/

# Copy frontend code and build
COPY frontend/ ./frontend/
RUN cd frontend && npm install && npm run build

# Create necessary directories
RUN mkdir -p /app/data /app/logs

# Expose ports
EXPOSE 8000 8001 3000

# Create startup script
COPY docker/start.sh ./start.sh
RUN chmod +x start.sh

# Set environment variables
ENV PYTHONPATH=/app/backend
ENV NODE_ENV=production

# Default command
CMD ["./start.sh"]