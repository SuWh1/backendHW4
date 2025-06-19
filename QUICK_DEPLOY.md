# 🚀 Quick Deploy Guide - A2A Voice Communication System

## 🔧 1. Droplet Setup (5 minutes)

SSH into your DigitalOcean droplet:
```bash
ssh root@YOUR_DROPLET_IP
```

Run the setup script:
```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/scripts/setup-droplet.sh -o setup.sh
chmod +x setup.sh
sudo ./setup.sh
```

## 🔑 2. SSH Key Setup

On your local machine:
```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"

# Copy to droplet
ssh-copy-id deploy@YOUR_DROPLET_IP

# Test connection
ssh deploy@YOUR_DROPLET_IP
```

## 🎛️ 3. GitHub Secrets Setup

Go to: **GitHub Repository → Settings → Secrets and variables → Actions**

Add these secrets:

### 🌐 Server Configuration
- `DO_HOST` = `YOUR_DROPLET_IP`
- `DO_USER` = `deploy`
- `DO_SSH_PRIVATE_KEY` = Contents of `~/.ssh/id_rsa` (your private key)

### 🗄️ Database Configuration
- `POSTGRES_DB` = `appdb`
- `POSTGRES_USER` = `postgres`
- `POSTGRES_PASSWORD` = `your-secure-password`

### ☁️ AWS Configuration (Optional)
- `AWS_ACCESS_KEY_ID` = `AKIA...`
- `AWS_SECRET_ACCESS_KEY` = `your-secret-key`
- `AWS_BUCKET_NAME` = `my-app-uploads`
- `AWS_REGION` = `us-east-1`

### 🤖 OpenAI Configuration
- `OPENAI_API_KEY` = `sk-proj-...`

## 🚀 4. Deploy

Push to main branch:
```bash
git add .
git commit -m "Deploy to production"
git push origin main
```

## 🔍 5. Verify Deployment

Check these URLs:
- **Frontend**: `http://YOUR_DROPLET_IP:3000`
- **Backend**: `http://YOUR_DROPLET_IP:8000`
- **API Docs**: `http://YOUR_DROPLET_IP:8000/docs`

## 📱 Quick Commands

```bash
# SSH to droplet
ssh deploy@YOUR_DROPLET_IP

# Check services
cd /opt/a2a-voice-app
docker-compose ps

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Health checks
curl http://localhost:8000/health
curl http://localhost:8000/health/openai
```

## 🆘 Troubleshooting

### GitHub Actions failing?
1. Check secrets are set correctly
2. Verify SSH key format (include `-----BEGIN` and `-----END` lines)
3. Check droplet allows SSH on port 22

### Services not starting?
```bash
# Check Docker status
sudo systemctl status docker

# Check logs
docker-compose logs

# Restart everything
docker-compose down && docker-compose up -d
```

### Can't access application?
```bash
# Check firewall
sudo ufw status

# Check ports
sudo netstat -tulpn | grep :3000
sudo netstat -tulpn | grep :8000
```

## 📋 Deployment Checklist

- [ ] DigitalOcean droplet created
- [ ] Setup script executed
- [ ] SSH keys configured
- [ ] GitHub secrets added
- [ ] Repository pushed to main
- [ ] GitHub Actions workflow completed
- [ ] Frontend accessible
- [ ] Backend API responding
- [ ] Voice communication working

**That's it! Your A2A Voice Communication System is deployed! 🎉** 