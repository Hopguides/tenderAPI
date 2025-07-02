# 🚀 Railway Deployment Guide za Tender API

## Quick Deploy na Railway

### 1. Pripravi projekt za deployment
```bash
# Ustvari Procfile za Railway
echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile

# Ustvari runtime.txt (opcijsko)
echo "python-3.11" > runtime.txt
```

### 2. Deploy na Railway
```bash
# Namesti Railway CLI
npm install -g @railway/cli

# Login v Railway
railway login

# Ustvari nov projekt
railway new

# Deploy
railway up
```

### 3. Nastavi environment variables
```bash
# Nastavi PORT (avtomatsko)
railway variables set PORT=8000

# Nastavi API ključe (opcijsko)
railway variables set SAM_API_KEY=your_sam_api_key
railway variables set TED_API_KEY=your_ted_api_key
```

### 4. Preveri deployment
```bash
# Dobi URL
railway domain

# Testiraj
curl https://your-app.railway.app/health
```

## Vercel Deployment (alternativa)

### 1. Ustvari vercel.json
```json
{
  "builds": [
    {
      "src": "main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "main.py"
    }
  ]
}
```

### 2. Deploy
```bash
# Namesti Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

## Test deployment
```bash
# Testiraj z našim test skriptom
python3 test_api.py https://your-app.railway.app
```

