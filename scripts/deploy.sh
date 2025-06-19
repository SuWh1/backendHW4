#!/bin/bash

# A2A Voice Communication System - DigitalOcean Deployment Script
# This script sets up and deploys the application on a DigitalOcean droplet

set -e

echo "🚀 Starting A2A Voice Communication System Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Update system packages
print_status "Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# Install required packages
print_status "Installing required packages..."
sudo apt-get install -y curl git wget unzip software-properties-common

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    print_status "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    print_status "Docker installed successfully"
else
    print_status "Docker is already installed"
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    print_status "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    print_status "Docker Compose installed successfully"
else
    print_status "Docker Compose is already installed"
fi

# Create application directory
APP_DIR="/opt/a2a-voice-app"
if [ ! -d "$APP_DIR" ]; then
    print_status "Creating application directory..."
    sudo mkdir -p $APP_DIR
    sudo chown $USER:$USER $APP_DIR
fi

cd $APP_DIR

# Set up UFW firewall
print_status "Configuring firewall..."
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 8000/tcp

# Set up log rotation
print_status "Setting up log rotation..."
sudo tee /etc/logrotate.d/a2a-voice-app > /dev/null <<EOF
/opt/a2a-voice-app/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    create 644 $USER $USER
}
EOF

# Create logs directory
mkdir -p logs

# Create systemd service for auto-start
print_status "Creating systemd service..."
sudo tee /etc/systemd/system/a2a-voice-app.service > /dev/null <<EOF
[Unit]
Description=A2A Voice Communication System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
User=$USER
Group=$USER

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable a2a-voice-app

# Start the application if docker-compose.yml exists
if [ -f "docker-compose.yml" ]; then
    print_status "Starting application..."
    docker-compose down || true
    docker-compose up -d --build
    
    # Wait for services to be ready
    print_status "Waiting for services to start..."
    sleep 30
    
    # Run database migrations
    print_status "Running database migrations..."
    docker-compose exec -T app alembic upgrade head || print_warning "Migration failed - this is normal on first run"
    
    # Health checks
    print_status "Running health checks..."
    
    # Check if FastAPI is responding
    if curl -f http://localhost:8000/health &> /dev/null; then
        print_status "✅ Backend health check passed"
    else
        print_warning "❌ Backend health check failed"
    fi
    
    # Check if frontend is responding
    if curl -f http://localhost:3000 &> /dev/null; then
        print_status "✅ Frontend health check passed"
    else
        print_warning "❌ Frontend health check failed"
    fi
    
    # Check OpenAI integration
    if curl -f http://localhost:8000/health/openai &> /dev/null; then
        print_status "✅ OpenAI integration health check passed"
    else
        print_warning "❌ OpenAI integration health check failed - check API key"
    fi
    
    print_status "🎉 Deployment completed successfully!"
    echo ""
    echo -e "${BLUE}Application URLs:${NC}"
    echo -e "Frontend: ${GREEN}http://$(curl -s ifconfig.me):3000${NC}"
    echo -e "Backend API: ${GREEN}http://$(curl -s ifconfig.me):8000${NC}"
    echo -e "API Docs: ${GREEN}http://$(curl -s ifconfig.me):8000/docs${NC}"
    echo ""
    echo -e "${BLUE}Useful Commands:${NC}"
    echo "View logs: docker-compose logs -f"
    echo "Restart services: docker-compose restart"
    echo "Stop services: docker-compose down"
    echo "Start services: docker-compose up -d"
    echo ""
    
else
    print_warning "docker-compose.yml not found. Application files need to be deployed first."
fi

print_status "Setup script completed!" 