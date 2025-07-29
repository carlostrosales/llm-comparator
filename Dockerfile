# Build frontend
FROM node:20 AS frontend-builder
WORKDIR /app/frontend
# Copy only dependency files
COPY frontend/package.json frontend/pnpm-lock.yaml* ./
RUN npm install -g pnpm@latest && pnpm install
# Copy source code
COPY frontend/ ./
RUN NODE_ENV=production pnpm run build

# Build backend
FROM python:3.12-slim
WORKDIR /app
# Copy only requirements
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir uv && uv pip install --system -r requirements.txt
# Copy backend code
COPY backend/ ./backend
# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist ./static

# Expose and run
ENV STATIC_DIR=/app/static
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug"]