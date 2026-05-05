FROM python:3.12-slim AS backend

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ backend/

# ── Frontend build stage ───────────────────────────────────────────────
FROM node:20-slim AS frontend

WORKDIR /app

COPY package.json ./
RUN npm install --production=false

COPY index.html vite.config.ts tsconfig.json tailwind.config.js postcss.config.js ./
COPY public/ public/
COPY src/ src/

RUN npm run build

# ── Final stage ────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

COPY --from=backend /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend /usr/local/bin /usr/local/bin
COPY --from=backend /app/backend backend/
COPY --from=frontend /app/dist static/

COPY requirements.txt .

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
