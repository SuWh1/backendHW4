#!/bin/bash

# Quick DigitalOcean Droplet Setup for A2A Voice Communication System
# Run this script on your fresh Ubuntu droplet

set -e

echo "🔧 Setting up DigitalOcean droplet for A2A Voice Communication System..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

# Update system
print_status "Updating system packages..."
apt-get update && apt-get upgrade -y

# Install essential packages
print_status "Installing essential packages..."
apt-get install -y curl git wget unzip software-properties-common ufw

# Create deploy user
print_status "Creating deploy user..."
if ! id "deploy" &>/dev/null; then
    adduser --disabled-password --gecos "" deploy
    usermod -aG sudo deploy
    print_status "✅ Deploy user created"
else
    print_status "Deploy user already exists"
fi

# Set up SSH directory for deploy user
print_status "Setting up SSH for deploy user..."
mkdir -p /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
touch /home/deploy/.ssh/authorized_keys
chmod 600 /home/deploy/.ssh/authorized_keys
chown -R deploy:deploy /home/deploy/.ssh

# Configure SSH
print_status "Configuring SSH..."
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl reload sshd

# Set up firewall
print_status "Configuring UFW firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 3000/tcp
ufw allow 8000/tcp
ufw --force enable

# Install Docker
print_status "Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker deploy
rm get-docker.sh

# Install Docker Compose
print_status "Installing Docker Compose..."
curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create application directory
print_status "Creating application directory..."
mkdir -p /opt/a2a-voice-app
chown deploy:deploy /opt/a2a-voice-app

# Create systemd service
print_status "Creating systemd service..."
cat > /etc/systemd/system/a2a-voice-app.service << EOF
[Unit]
Description=A2A Voice Communication System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/a2a-voice-app
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
User=deploy
Group=deploy

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable a2a-voice-app

# Set up log rotation
print_status "Setting up log rotation..."
cat > /etc/logrotate.d/a2a-voice-app << EOF
/opt/a2a-voice-app/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    create 644 deploy deploy
}
EOF

# Create logs directory
mkdir -p /opt/a2a-voice-app/logs
chown deploy:deploy /opt/a2a-voice-app/logs

# Install fail2ban for security
print_status "Installing fail2ban for security..."
apt-get install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban

print_status "🎉 Droplet setup completed!"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "1. Add your SSH public key to deploy user:"
echo "   ssh-copy-id deploy@$(curl -s ifconfig.me)"
echo ""
echo "2. Test SSH connection:"
echo "   ssh deploy@$(curl -s ifconfig.me)"
echo ""
echo "3. Set up GitHub repository secrets with:"
echo "   DO_HOST: $(curl -s ifconfig.me)"
echo "   DO_USER: deploy"
echo "   DO_SSH_PRIVATE_KEY: (your private key)"
echo ""
echo "4. Configure your environment variables in GitHub secrets"
echo ""
echo "5. Push to main branch to trigger deployment!"
echo ""
echo -e "${YELLOW}Droplet IP:${NC} $(curl -s ifconfig.me)" 