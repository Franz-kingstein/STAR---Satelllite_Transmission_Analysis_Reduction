# STAR Analysis - Docker README
# One-Command Deployment Instructions

## 🚀 Quick Start

### Option 1: One-Command Deployment (Recommended)
```bash
curl -sSL https://raw.githubusercontent.com/Franz-kingstein/STAR---Satelllite_Transmission_Analysis_Reduction/main/deploy.sh | bash
```

### Option 2: Manual Deployment
```bash
# Download configuration
curl -O https://raw.githubusercontent.com/Franz-kingstein/STAR---Satelllite_Transmission_Analysis_Reduction/main/docker-compose.prod.yml

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

## 🌐 Access
- **Web Application**: http://localhost:8501
- **Database**: localhost:27017

## 📊 What's Included
- Interactive Streamlit web application
- MongoDB database with 118,000+ star records
- Automated data import and setup
- Production-ready configuration

## 🛠️ Management Commands
```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop application
docker-compose -f docker-compose.prod.yml down

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Update to latest version
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## 📋 System Requirements
- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM available
- 2GB+ disk space

## 🔧 Troubleshooting
1. **Application not loading**: Wait 2-3 minutes for data import
2. **Port conflicts**: Ensure ports 8501 and 27017 are free
3. **Performance issues**: Allocate more RAM to Docker

## 📚 Documentation
Complete project documentation available at:
https://github.com/Franz-kingstein/STAR---Satelllite_Transmission_Analysis_Reduction
