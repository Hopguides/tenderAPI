# 🚀 Tender API - Railway Deployment Guide

## 📋 Quick Deploy

### 1. Railway Setup
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Create new project
railway new tender-api

# Deploy
railway up
```

### 2. Environment Variables
```bash
# Set SAM.gov API key (optional - for US deployment)
railway variables set SAM_API_KEY="PQlc5kMEBFTzy6cQJIIli0EwKxBvBpMILbYAIR9p"

# Set custom port (optional)
railway variables set PORT="8000"
```

### 3. Custom Domain (optional)
```bash
# Generate Railway domain
railway domain

# Or set custom domain
railway domain add your-domain.com
```

## 🔧 Configuration

### Procfile
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Requirements.txt
- FastAPI 0.104.1
- Uvicorn 0.24.0
- HTTPx 0.25.2
- BeautifulSoup4 4.12.2
- Pydantic 2.5.0

## 📊 Features

### Available Endpoints
- `GET /` - API information
- `GET /platforms` - Platform details
- `GET /health` - Health check
- `POST /search/{platform}` - Platform search
- `GET /quick/{platform}` - Quick search

### Supported Platforms
- **TED Europe** - European tenders
- **SAM.gov** - US government contracts
- **Bonfire** - US state & municipal

## 🧪 Testing

### Local Test
```bash
# Start server
uvicorn main:app --reload

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/platforms
```

### Production Test
```bash
# Test deployed API
curl https://your-app.railway.app/health
curl https://your-app.railway.app/platforms
```

## 🔍 Monitoring

### Health Check
```bash
curl https://your-app.railway.app/health
```

### Platform Status
```bash
curl https://your-app.railway.app/platforms
```

## 📝 Notes

- **SAM.gov API** requires US IP address
- **TED Europe** works globally
- **Bonfire** works globally
- All platforms have graceful error handling

## 🎯 Success Indicators

✅ Health check returns 200
✅ Platforms endpoint lists 3 platforms
✅ Search endpoints respond correctly
✅ Error handling works gracefully

Your Tender API is ready for production! 🎉

