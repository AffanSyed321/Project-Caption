# Stage 1: Build Frontend
FROM node:18-alpine as frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Build Backend & Serve
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend assets from Stage 1
COPY --from=frontend-build /app/frontend/dist ./backend/static

# Set environment variables
ENV PYTHONPATH=/app/backend
ENV PORT=8000

# Run the application
# Increased timeout to 180s for AI operations (caption generation can take 30-90 seconds)
# Graceful timeout set to 200s to allow requests to complete
CMD ["gunicorn", "backend.app.main:app", \
     "--workers", "2", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "180", \
     "--graceful-timeout", "200", \
     "--keep-alive", "5"]
