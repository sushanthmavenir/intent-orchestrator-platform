# Deployment Guide

This guide provides comprehensive instructions for deploying the Intent Orchestration Platform in various environments.

## 📋 Prerequisites

### System Requirements

- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 50GB available space
- **Network**: Internet access for downloading dependencies

### Software Requirements

- **Python**: 3.11 or higher
- **Node.js**: 18 or higher
- **Docker**: 20.10 or higher (optional)
- **Docker Compose**: 2.0 or higher (optional)

## 🚀 Deployment Options

### Option 1: Development Deployment

For local development and testing:

```bash
# Clone repository
git clone <repository-url>
cd intent-orchestrator-platform

# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Start services
python start_server.py  # Backend
npm start --prefix frontend  # Frontend
```

### Option 2: Docker Development

Quick setup with hot reloading:

```bash
docker-compose -f docker/docker-development.yml up -d
```

### Option 3: Production Docker

Full production deployment:

```bash
docker-compose up -d
```

### Option 4: Manual Production

Step-by-step production setup:

1. **Prepare Environment**
   ```bash
   # Create application user
   sudo useradd -m -s /bin/bash intent-platform
   sudo su - intent-platform
   
   # Clone repository
   git clone <repository-url>
   cd intent-orchestrator-platform
   ```

2. **Install Dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

3. **Configure Database**
   ```bash
   # For PostgreSQL
   createdb intent_orchestrator
   psql intent_orchestrator < docker/init-db.sql
   ```

4. **Build Frontend**
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

5. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with production values
   ```

6. **Start Services**
   ```bash
   # Using systemd service files (recommended)
   sudo systemctl enable intent-platform
   sudo systemctl start intent-platform
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with production settings:

```env
# Environment
NODE_ENV=production
PYTHONPATH=/app/backend

# Database
DATABASE_URL=postgresql://intent_user:password@localhost:5432/intent_orchestrator

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CAMARA_PORT=8001

# SSL/TLS
SSL_CERT_PATH=/etc/ssl/certs/intent-platform.crt
SSL_KEY_PATH=/etc/ssl/private/intent-platform.key

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/intent-platform/app.log
```

### Database Configuration

#### PostgreSQL Setup

```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres createuser --interactive intent_user
sudo -u postgres createdb intent_orchestrator
sudo -u postgres psql -c "ALTER USER intent_user PASSWORD 'secure_password';"

# Grant permissions
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE intent_orchestrator TO intent_user;"

# Initialize schema
psql -U intent_user -d intent_orchestrator -f docker/init-db.sql
```

#### Redis Setup

```bash
# Install Redis
sudo apt install redis-server

# Configure Redis
sudo nano /etc/redis/redis.conf
# Set: bind 127.0.0.1 ::1
# Set: requirepass your_redis_password

# Start Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/intent-platform
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/intent-platform.crt;
    ssl_certificate_key /etc/ssl/private/intent-platform.key;

    # Frontend
    location / {
        root /opt/intent-platform/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # CAMARA APIs
    location /camara/ {
        proxy_pass http://localhost:8001/camara/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Systemd Service

Create `/etc/systemd/system/intent-platform.service`:

```ini
[Unit]
Description=Intent Orchestration Platform
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=intent-platform
Group=intent-platform
WorkingDirectory=/opt/intent-platform
Environment=PYTHONPATH=/opt/intent-platform/backend
ExecStart=/opt/intent-platform/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/camara-apis.service`:

```ini
[Unit]
Description=CAMARA Mock APIs
After=network.target

[Service]
Type=exec
User=intent-platform
Group=intent-platform
WorkingDirectory=/opt/intent-platform/backend
Environment=PYTHONPATH=/opt/intent-platform/backend
ExecStart=/opt/intent-platform/venv/bin/python -m uvicorn camara_apis.main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

## 🔒 Security Configuration

### SSL/TLS Setup

```bash
# Generate self-signed certificate (development)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/intent-platform.key \
  -out /etc/ssl/certs/intent-platform.crt

# For production, use Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Firewall Configuration

```bash
# Configure UFW
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Internal services (if needed)
sudo ufw allow from 10.0.0.0/8 to any port 8000
sudo ufw allow from 10.0.0.0/8 to any port 8001
```

### Application Security

1. **Authentication**: Implement OAuth2/JWT
2. **Rate Limiting**: Configure in Nginx or application
3. **Input Validation**: Ensure all inputs are validated
4. **Secrets Management**: Use environment variables or secret management systems

## 📊 Monitoring Setup

### Prometheus Configuration

```yaml
# /etc/prometheus/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'intent-platform'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboard

1. **Install Grafana**
   ```bash
   sudo apt install -y software-properties-common
   sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
   sudo apt update
   sudo apt install grafana
   ```

2. **Configure Grafana**
   ```bash
   sudo systemctl enable grafana-server
   sudo systemctl start grafana-server
   ```

3. **Access Grafana**: http://localhost:3000 (admin/admin)

### Log Management

```bash
# Configure logrotate
sudo nano /etc/logrotate.d/intent-platform

/var/log/intent-platform/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 intent-platform intent-platform
}
```

## 🔄 CI/CD Pipeline

### GitHub Actions Example

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          python -m spacy download en_core_web_sm
          
      - name: Run tests
        run: python test_integration.py
        
      - name: Build Docker image
        run: docker build -t intent-platform:latest .
        
      - name: Deploy to production
        run: |
          # Add deployment commands here
          echo "Deploying to production..."
```

## 🚀 Deployment Verification

### Health Checks

```bash
# Check service status
curl -f http://localhost:8000/health
curl -f http://localhost:8001/health

# Check database connection
psql -U intent_user -d intent_orchestrator -c "SELECT version();"

# Check Redis connection
redis-cli ping
```

### Integration Tests

```bash
# Run comprehensive tests
python test_integration.py

# Check specific endpoints
curl -X GET http://localhost:8000/tmf921/intent
curl -X GET http://localhost:8000/api/agents/health
```

### Performance Testing

```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test API performance
ab -n 1000 -c 10 http://localhost:8000/health

# Test WebSocket connections
# Use custom WebSocket load testing tools
```

## 🔧 Maintenance

### Regular Tasks

1. **Database Maintenance**
   ```bash
   # Vacuum and analyze
   psql -U intent_user -d intent_orchestrator -c "VACUUM ANALYZE;"
   
   # Backup
   pg_dump -U intent_user intent_orchestrator > backup_$(date +%Y%m%d).sql
   ```

2. **Log Rotation**
   ```bash
   sudo logrotate /etc/logrotate.d/intent-platform
   ```

3. **Security Updates**
   ```bash
   sudo apt update && sudo apt upgrade
   pip install --upgrade -r requirements.txt
   ```

### Scaling

#### Horizontal Scaling

```yaml
# docker-compose.yml additions
version: '3.8'
services:
  intent-platform:
    deploy:
      replicas: 3
      
  nginx:
    depends_on:
      - intent-platform
    # Load balancer configuration
```

#### Vertical Scaling

```yaml
# Resource limits
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 8G
    reservations:
      cpus: '2.0'
      memory: 4G
```

## 🆘 Troubleshooting

### Common Issues

1. **Service Won't Start**
   ```bash
   # Check logs
   sudo journalctl -u intent-platform -f
   
   # Check file permissions
   sudo chown -R intent-platform:intent-platform /opt/intent-platform
   ```

2. **Database Connection Issues**
   ```bash
   # Test connection
   psql -U intent_user -h localhost -d intent_orchestrator
   
   # Check PostgreSQL status
   sudo systemctl status postgresql
   ```

3. **Performance Issues**
   ```bash
   # Monitor resources
   htop
   
   # Check application metrics
   curl http://localhost:8000/metrics
   ```

### Recovery Procedures

1. **Database Recovery**
   ```bash
   # Restore from backup
   psql -U intent_user -d intent_orchestrator < backup_20240101.sql
   ```

2. **Service Recovery**
   ```bash
   # Restart services
   sudo systemctl restart intent-platform
   sudo systemctl restart camara-apis
   sudo systemctl restart nginx
   ```

This deployment guide provides a comprehensive foundation for deploying the Intent Orchestration Platform in production environments with proper security, monitoring, and maintenance procedures.