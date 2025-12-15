# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Python runtime
FROM python:3.11-slim
WORKDIR /app

# Copy frontend build from stage 1
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY dashboard/ ./dashboard/
COPY *.py .

# Expose port
EXPOSE 8080

# Run gunicorn
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:8080", "dashboard.api:app", "--timeout", "120"]