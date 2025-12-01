# Combined Dockerfile for Cloud Run deployment
# Builds frontend and serves it with the FastAPI backend

# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Backend with frontend static files
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy frontend build to static directory
COPY --from=frontend-build /frontend/dist ./static

# Cloud Run uses PORT env var (default 8080)
ENV PORT=8080

# Run with gunicorn for production
CMD exec gunicorn main:app -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT --timeout 300
