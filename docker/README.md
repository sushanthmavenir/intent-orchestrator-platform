# Docker Deployment Guide

This directory contains Docker configuration files for deploying the Intent Orchestration Platform in various environments.

## Quick Start

### Development Environment
For local development with hot reloading:

```bash
# Start development environment
docker-compose -f docker/docker-development.yml up -d

# View logs
docker-compose -f docker/docker-development.yml logs -f

# Stop environment
docker-compose -f docker/docker-development.yml down
```

### Production Environment
For full production deployment:

```bash
# Build and start all services
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f intent-platform

# Stop all services
docker-compose down
```

## Service Architecture

### Core Services

#### intent-platform
- **Purpose**: Main application container
- **Ports**: 8000 (API), 8001 (CAMARA), 3000 (Frontend)
- **Components**:
  - FastAPI backend with TMF 921A APIs
  - CAMARA mock APIs
  - React frontend (development mode)
  - All specialized agents
  - Workflow orchestration engine

#### redis
- **Purpose**: Caching and session management
- **Port**: 6379
- **Use Cases**:
  - API response caching
  - WebSocket session management
  - Agent performance metrics storage

#### postgres
- **Purpose**: Production database
- **Port**: 5432
- **Features**:
  - TMF 921A intent storage
  - Agent registry and metrics
  - Fraud case management
  - Workflow execution history

#### nginx
- **Purpose**: Reverse proxy and load balancer
- **Ports**: 80 (HTTP), 443 (HTTPS)
- **Features**:
  - Static file serving
  - API routing
  - WebSocket proxying
  - Rate limiting
  - SSL termination

### Monitoring Services

#### prometheus
- **Purpose**: Metrics collection
- **Port**: 9090
- **Metrics**:
  - Application performance
  - Agent health and response times
  - API endpoint statistics
  - System resource usage

#### grafana
- **Purpose**: Monitoring dashboards
- **Port**: 3001
- **Default Login**: admin/admin
- **Dashboards**:
  - Platform overview
  - Agent performance
  - Fraud detection metrics
  - System health

## Environment Configuration

### Environment Variables

#### Development
```bash
NODE_ENV=development
PYTHONPATH=/app/backend
PYTHONUNBUFFERED=1
RELOAD=true
```

#### Production
```bash
NODE_ENV=production
PYTHONPATH=/app/backend
PYTHONUNBUFFERED=1
DATABASE_URL=postgresql://intent_user:intent_password@postgres:5432/intent_orchestrator
REDIS_URL=redis://redis:6379
```

### Volume Mounts

#### Development
- Source code mounted for hot reloading
- Data directory for SQLite database
- Logs directory for debugging

#### Production
- Named volumes for data persistence
- Configuration files mounted read-only
- Log aggregation to external systems

## Service URLs

### Development Environment
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **CAMARA APIs**: http://localhost:8001
- **SQLite Browser**: http://localhost:3001
- **Redis**: localhost:6379

### Production Environment
- **Main Application**: http://localhost (via Nginx)
- **API**: http://localhost/api
- **WebSocket**: ws://localhost/ws
- **Monitoring**: http://localhost:9090 (Prometheus)
- **Dashboards**: http://localhost:3001 (Grafana)

## Health Checks

All services include health checks:

```bash
# Check platform health
curl http://localhost:8000/health

# Check all service status
docker-compose ps

# Detailed health information
docker-compose exec intent-platform curl localhost:8000/health
```

## Data Persistence

### Development
- SQLite database in `./data` directory
- Logs in `./logs` directory
- Redis data in named volume

### Production
- PostgreSQL data in `postgres_data` volume
- Redis data in `redis_data` volume
- Application data in `intent_data` volume
- Nginx logs in `nginx_logs` volume
- Monitoring data in respective volumes

## Scaling and Load Balancing

### Horizontal Scaling
```bash
# Scale main application
docker-compose up -d --scale intent-platform=3

# Use external load balancer for production
# Configure Nginx upstream for multiple instances
```

### Resource Limits
```yaml
# Add to service configuration
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      cpus: '1.0'
      memory: 2G
```

## Security Considerations

### Production Security
- Use strong passwords for database
- Enable SSL/TLS for external access
- Configure firewall rules
- Use secrets management for sensitive data
- Regular security updates

### Network Security
```yaml
# Custom network configuration
networks:
  intent-network:
    driver: bridge
    internal: true  # Restrict external access
```

## Backup and Recovery

### Database Backup
```bash
# PostgreSQL backup
docker-compose exec postgres pg_dump -U intent_user intent_orchestrator > backup.sql

# Restore from backup
docker-compose exec -T postgres psql -U intent_user intent_orchestrator < backup.sql
```

### Volume Backup
```bash
# Backup all volumes
docker run --rm -v intent_data:/data -v $(pwd):/backup busybox tar czf /backup/intent_data.tar.gz /data
```

## Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs
docker-compose logs intent-platform

# Check container status
docker-compose ps

# Rebuild container
docker-compose build --no-cache intent-platform
```

#### Service Communication Issues
```bash
# Test network connectivity
docker-compose exec intent-platform ping redis
docker-compose exec intent-platform curl postgres:5432

# Check service discovery
docker network ls
docker network inspect intent-orchestrator-network
```

#### Performance Issues
```bash
# Monitor resource usage
docker stats

# Check application metrics
curl http://localhost:8000/metrics

# View detailed logs
docker-compose logs -f --tail=100 intent-platform
```

### Debug Mode

Enable debug mode for troubleshooting:

```bash
# Set debug environment
export DEBUG=true
export LOG_LEVEL=DEBUG

# Restart with debug logging
docker-compose up -d
```

## Development Workflow

### Code Changes
1. Modify source code
2. Changes automatically reload (development mode)
3. Test changes at http://localhost:3000
4. Check logs for errors

### Adding New Services
1. Update `docker-compose.yml`
2. Add service configuration
3. Update network and volume configurations
4. Test service integration

### Database Migrations
```bash
# Access database
docker-compose exec postgres psql -U intent_user intent_orchestrator

# Run custom migrations
docker-compose exec intent-platform python manage.py migrate
```

## Production Deployment

### Deployment Checklist
- [ ] SSL certificates configured
- [ ] Environment variables set
- [ ] Database initialized
- [ ] Monitoring configured
- [ ] Backup procedures tested
- [ ] Security hardening applied
- [ ] Performance testing completed

### Rolling Updates
```bash
# Update with zero downtime
docker-compose pull
docker-compose up -d --no-deps intent-platform
```

This Docker setup provides a complete, production-ready deployment of the Intent Orchestration Platform with monitoring, scaling, and security features.