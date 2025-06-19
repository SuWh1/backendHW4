# 🚀 CI/CD Deployment Guide - A2A Voice Communication System

This guide will help you set up automated deployment to your DigitalOcean droplet using GitHub Actions.

## 📋 Prerequisites

- DigitalOcean droplet (Ubuntu 20.04+ recommended)
- GitHub repository
- SSH access to your droplet
- Domain name (optional, but recommended)

## 🔧 Initial DigitalOcean Droplet Setup

### 1. Connect to Your Droplet

```bash
ssh root@your-droplet-ip
```

### 2. Create a Non-Root User

```bash
# Create user
adduser deploy
usermod -aG sudo deploy

# Switch to deploy user
su - deploy
```

### 3. Set Up SSH Key Authentication

On your local machine:
```bash
# Generate SSH key pair (if you don't have one)
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"

# Copy public key to droplet
ssh-copy-id deploy@your-droplet-ip
```

### 4. Run Initial Setup Script

```bash
# Download and run the setup script
curl -fsSL https://raw.githubusercontent.com/your-username/your-repo/main/scripts/deploy.sh -o deploy.sh
chmod +x deploy.sh
./deploy.sh
```

## ⚙️ GitHub Repository Setup

### 1. Required Repository Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions, and add:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `DO_HOST` | DigitalOcean droplet IP | `167.99.123.456` |
| `DO_USER` | SSH username | `deploy` |
| `DO_SSH_PRIVATE_KEY` | SSH private key | Contents of `~/.ssh/id_rsa` |
| `POSTGRES_DB` | Database name | `appdb` |
| `POSTGRES_USER` | Database username | `postgres` |
| `POSTGRES_PASSWORD` | Database password | `your-secure-password` |
| `AWS_ACCESS_KEY_ID` | AWS access key | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | `your-secret-key` |
| `AWS_BUCKET_NAME` | S3 bucket name | `my-app-uploads` |
| `AWS_REGION` | AWS region | `us-east-1` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-proj-...` |

### 2. Getting Your SSH Private Key

```bash
# On your local machine
cat ~/.ssh/id_rsa
```

Copy the entire output (including `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----`) and paste it as the `DO_SSH_PRIVATE_KEY` secret.

## 🔄 CI/CD Pipeline Overview

The GitHub Actions workflow (`deploy.yml`) will:

1. **Test Stage**:
   - Install Python dependencies
   - Install Node.js dependencies
   - Build frontend
   - Run basic validation

2. **Deploy Stage** (only on `main` branch):
   - Create deployment package
   - Copy files to DigitalOcean droplet
   - Create environment file with secrets
   - Deploy using Docker Compose
   - Run database migrations
   - Perform health checks

## 🚀 Deployment Process

### Automatic Deployment

Every push to the `main` branch will trigger automatic deployment:

```bash
git add .
git commit -m "Update application"
git push origin main
```

### Manual Deployment

You can also trigger deployment manually:

1. Go to your GitHub repository
2. Click "Actions" tab
3. Select "Deploy to DigitalOcean" workflow
4. Click "Run workflow"

## 🔍 Monitoring Deployment

### GitHub Actions Logs

1. Go to repository → Actions
2. Click on the latest workflow run
3. Expand job steps to see detailed logs

### Server Logs

SSH into your droplet and check:

```bash
# Check application logs
cd /opt/a2a-voice-app
docker-compose logs -f

# Check specific service logs
docker-compose logs app
docker-compose logs frontend
docker-compose logs db
```

### Health Checks

After deployment, verify services:

```bash
# Backend health
curl http://your-droplet-ip:8000/health

# OpenAI integration
curl http://your-droplet-ip:8000/health/openai

# Frontend
curl http://your-droplet-ip:3000
```

## 🌐 Production URLs

After successful deployment:

- **Frontend**: `http://your-droplet-ip:3000`
- **Backend API**: `http://your-droplet-ip:8000`
- **API Documentation**: `http://your-droplet-ip:8000/docs`

## 🔧 Common Issues & Solutions

### 1. SSH Connection Failed

**Problem**: GitHub Actions can't connect to droplet

**Solutions**:
- Verify `DO_HOST`, `DO_USER`, and `DO_SSH_PRIVATE_KEY` secrets
- Ensure SSH key is properly formatted (with line breaks)
- Check if UFW firewall allows SSH (port 22)

### 2. Docker Permission Denied

**Problem**: Docker commands fail with permission errors

**Solutions**:
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in
```

### 3. Port Already in Use

**Problem**: Services can't bind to ports

**Solutions**:
```bash
# Check what's using the port
sudo netstat -tulpn | grep :8000

# Stop conflicting services
docker-compose down
```

### 4. Database Migration Failed

**Problem**: Alembic migration errors

**Solutions**:
```bash
# Reset database (CAUTION: destroys data)
docker-compose down -v
docker-compose up -d
```

### 5. OpenAI Health Check Failed

**Problem**: OpenAI API key not working

**Solutions**:
- Verify `OPENAI_API_KEY` secret is correct
- Check API key has sufficient credits
- Ensure key has proper permissions

## 🔒 Security Best Practices

1. **Firewall Configuration**:
   ```bash
   sudo ufw enable
   sudo ufw allow ssh
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw allow 3000
   sudo ufw allow 8000
   ```

2. **Regular Updates**:
   ```bash
   # Update system packages
   sudo apt update && sudo apt upgrade -y
   
   # Update Docker images
   docker-compose pull
   docker-compose up -d
   ```

3. **SSL/TLS** (Recommended):
   - Set up Let's Encrypt SSL certificate
   - Configure nginx with HTTPS
   - Update frontend to use HTTPS

## 📱 Manual Commands

### Service Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f

# Update and restart
git pull origin main
docker-compose up -d --build
```

### Database Management

```bash
# Access database
docker-compose exec db psql -U postgres -d appdb

# Backup database
docker-compose exec db pg_dump -U postgres appdb > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T db psql -U postgres -d appdb
```

## 🎯 Next Steps

1. **Domain Setup**: Configure a domain name to point to your droplet
2. **SSL Certificate**: Set up HTTPS with Let's Encrypt
3. **Monitoring**: Add application monitoring (e.g., Prometheus, Grafana)
4. **Backup Strategy**: Implement regular database backups
5. **Load Balancing**: Scale with multiple droplets behind a load balancer

## 📞 Support

If you encounter issues:

1. Check GitHub Actions logs
2. Check server logs: `docker-compose logs -f`
3. Verify all secrets are set correctly
4. Ensure droplet has sufficient resources (2GB RAM minimum recommended)

Happy deploying! 🚀 