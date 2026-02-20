# Deployment Guide

Guide for deploying MemNexus in production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Production Setup](#production-setup)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Security](#security)
- [Backup and Recovery](#backup-and-recovery)

## Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8+ GB |
| Disk | 10 GB | 50+ GB SSD |
| Network | 100 Mbps | 1 Gbps |

### Software Requirements

- Python 3.12+
- PostgreSQL 14+ (optional, for metadata)
- Redis 7+ (optional, for caching)
- Node.js 18+ (for frontend)
- Docker 20.10+ (optional)

## Production Setup

### 1. Environment Setup

Create a dedicated user:
```bash
sudo useradd -r -s /bin/false memnexus
sudo mkdir -p /opt/memnexus
sudo chown memnexus:memnexus /opt/memnexus
```

### 2. Install Dependencies

```bash
cd /opt/memnexus
git clone https://github.com/Leeelics/MemNexus.git .
pip install -e ".[dev]"
```

### 3. Configure Environment

Create production config:
```bash
sudo mkdir -p /etc/memnexus
sudo tee /etc/memnexus/config.env > /dev/null << 'EOF'
# Security
MEMNEXUS_SECRET_KEY=$(openssl rand -hex 32)
MEMNEXUS_ENV=production

# Server
MEMNEXUS_HOST=0.0.0.0
MEMNEXUS_PORT=8080

# Data
MEMNEXUS_DATA_DIR=/var/lib/memnexus

# Database (PostgreSQL recommended)
MEMNEXUS_DATABASE_URL=postgresql+asyncpg://memnexus:${DB_PASSWORD}@localhost:5432/memnexus

# Redis
MEMNEXUS_REDIS_URL=redis://localhost:6379/0

# Limits
MEMNEXUS_AGENT_TIMEOUT=600
MEMNEXUS_AGENT_MAX_RETRIES=5
EOF
```

### 4. Create Systemd Service

```bash
sudo tee /etc/systemd/system/memnexus.service > /dev/null << 'EOF'
[Unit]
Description=MemNexus Multi-Agent Collaboration System
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=memnexus
Group=memnexus
WorkingDirectory=/opt/memnexus
Environment="PATH=/opt/memnexus/venv/bin"
EnvironmentFile=/etc/memnexus/config.env
ExecStart=/opt/memnexus/venv/bin/memnexus server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable memnexus
sudo systemctl start memnexus
```

### 5. Setup Frontend

```bash
cd /opt/memnexus/frontend
npm install
npm run build
```

Serve with Nginx (see [Nginx Configuration](#nginx-configuration)).

## Docker Deployment

### Quick Start

```bash
# Clone repository
git clone https://github.com/Leeelics/MemNexus.git
cd MemNexus

# Start with docker-compose
docker-compose up -d
```

### Dockerfile

```dockerfile
# Backend
FROM python:3.12-slim as backend

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY pyproject.toml .
RUN pip install -e .

EXPOSE 8080

CMD ["memnexus", "server", "--host", "0.0.0.0"]

# Frontend
FROM node:18-alpine as frontend

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

FROM nginx:alpine
COPY --from=frontend /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

### Docker Compose

```yaml
version: '3.8'

services:
  memnexus:
    build:
      context: .
      target: backend
    ports:
      - "8080:8080"
    environment:
      - MEMNEXUS_SECRET_KEY=${SECRET_KEY}
      - MEMNEXUS_DATABASE_URL=postgresql+asyncpg://memnexus:${DB_PASSWORD}@postgres:5432/memnexus
      - MEMNEXUS_REDIS_URL=redis://redis:6379/0
    volumes:
      - memnexus_data:/var/lib/memnexus
    depends_on:
      - postgres
      - redis

  frontend:
    build:
      context: .
      target: frontend
    ports:
      - "3000:80"
    depends_on:
      - memnexus

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=memnexus
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=memnexus
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  memnexus_data:
  postgres_data:
  redis_data:
```

## Kubernetes Deployment

### Namespace

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: memnexus
```

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: memnexus-config
  namespace: memnexus
data:
  MEMNEXUS_HOST: "0.0.0.0"
  MEMNEXUS_PORT: "8080"
  MEMNEXUS_ENV: "production"
```

### Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: memnexus-secrets
  namespace: memnexus
type: Opaque
stringData:
  MEMNEXUS_SECRET_KEY: "your-secret-key-here"
  MEMNEXUS_DATABASE_URL: "postgresql+asyncpg://memnexus:password@postgres:5432/memnexus"
  MEMNEXUS_REDIS_URL: "redis://redis:6379/0"
```

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: memnexus
  namespace: memnexus
spec:
  replicas: 1
  selector:
    matchLabels:
      app: memnexus
  template:
    metadata:
      labels:
        app: memnexus
    spec:
      containers:
      - name: memnexus
        image: memnexus:latest
        ports:
        - containerPort: 8080
        envFrom:
        - configMapRef:
            name: memnexus-config
        - secretRef:
            name: memnexus-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        volumeMounts:
        - name: data
          mountPath: /var/lib/memnexus
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: memnexus-data
```

### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: memnexus
  namespace: memnexus
spec:
  selector:
    app: memnexus
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
```

### Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: memnexus
  namespace: memnexus
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - memnexus.example.com
    secretName: memnexus-tls
  rules:
  - host: memnexus.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: memnexus
            port:
              number: 80
```

## Configuration

### Nginx Configuration

```nginx
upstream memnexus {
    server 127.0.0.1:8080;
}

upstream frontend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name memnexus.example.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name memnexus.example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # API
    location /api/ {
        proxy_pass http://memnexus;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # WebSocket
    location /ws/ {
        proxy_pass http://memnexus;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Monitoring

### Health Checks

```bash
# API health
curl http://localhost:8080/health

# Memory store
curl http://localhost:8080/api/v1/memory/stats
```

### Prometheus Metrics

Enable metrics endpoint:
```bash
export MEMNEXUS_METRICS_ENABLED=true
export MEMNEXUS_METRICS_PORT=9090
```

### Logging

Configure log rotation:
```bash
sudo tee /etc/logrotate.d/memnexus > /dev/null << 'EOF'
/var/log/memnexus/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 memnexus memnexus
}
EOF
```

## Security

### SSL/TLS

Generate certificates:
```bash
certbot certonly --standalone -d memnexus.example.com
```

### Firewall

```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow API (if needed)
sudo ufw allow 8080/tcp
```

### API Authentication

Enable API key authentication:
```bash
export MEMNEXUS_API_KEY_REQUIRED=true
export MEMNEXUS_API_KEYS="key1,key2,key3"
```

## Backup and Recovery

### Automated Backups

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/memnexus"

# Backup LanceDB
tar czf $BACKUP_DIR/lancedb_$DATE.tar.gz /var/lib/memnexus/memory.lance

# Backup PostgreSQL
pg_dump memnexus > $BACKUP_DIR/postgres_$DATE.sql

# Cleanup old backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
```

Add to crontab:
```bash
0 2 * * * /opt/memnexus/scripts/backup.sh
```

### Recovery

```bash
# Restore LanceDB
tar xzf lancedb_20260220_120000.tar.gz -C /

# Restore PostgreSQL
psql memnexus < postgres_20260220_120000.sql
```

## Scaling

### Horizontal Scaling

For high availability, deploy multiple instances:

```yaml
# deployment.yaml
spec:
  replicas: 3
```

Use Redis for shared state:
```bash
export MEMNEXUS_REDIS_URL=redis://redis-cluster:6379/0
```

### Load Balancing

Use Nginx or HAProxy for load balancing:
```nginx
upstream memnexus_backend {
    server 10.0.1.10:8080;
    server 10.0.1.11:8080;
    server 10.0.1.12:8080;
}
```

## Troubleshooting

### Check Service Status

```bash
sudo systemctl status memnexus
sudo journalctl -u memnexus -f
```

### Check Logs

```bash
tail -f /var/log/memnexus/server.log
tail -f /var/log/memnexus/error.log
```

### Database Connection

```bash
# Test PostgreSQL connection
psql $MEMNEXUS_DATABASE_URL -c "SELECT 1;"

# Test Redis connection
redis-cli -u $MEMNEXUS_REDIS_URL ping
```

## Upgrade

### Zero-Downtime Upgrade

```bash
# 1. Deploy new version
sudo systemctl reload memnexus

# 2. Or using blue-green deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps --scale memnexus=2 memnexus
```

---

For more information, see:
- [Getting Started](GETTING_STARTED.md)
- [API Reference](API.md)
- [Architecture Overview](ARCHITECTURE.md)
