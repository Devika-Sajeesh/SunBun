# Dockerfile for Aegra Backend
# Build an environment for the SunBun Solar Assistant

FROM python:3.10-slim

WORKDIR /app

# Install dependencies first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["aegra", "dev"]
