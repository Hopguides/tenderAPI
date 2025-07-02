# 🗄️ Supabase Integration Guide
## Tender API Database Integration

Tender API je bil uspešno integriran s Supabase PostgreSQL bazo za avtomatsko shranjevanje tender rezultatov.

## 🚀 **IMPLEMENTIRANE FUNKCIONALNOSTI:**

### **1. Avtomatsko shranjevanje tender rezultatov**
- ✅ **SAM.gov** - Avtomatsko shranjevanje vseh search rezultatov
- ✅ **TED Europe** - Avtomatsko shranjevanje vseh search rezultatov  
- ✅ **Bonfire** - Avtomatsko shranjevanje vseh search rezultatov
- ✅ **Search logging** - Sledenje vseh search operacij

### **2. Database modeli**
- ✅ **TenderListing** - Glavna tabela za tender objave
- ✅ **SearchLog** - Tabela za sledenje search operacij
- ✅ **UUID primary keys** - Unikatni identifikatorji
- ✅ **JSON storage** - Raw data shranjevanje

### **3. API Endpoints za testiranje**
- ✅ **`/database/status`** - Database connection status
- ✅ **`/database/tenders`** - Pregled shranjenih tenders
- ✅ **`/database/test-save`** - Test shranjevanja
- ✅ **`/database/search-logs`** - Search history

## 🔧 **KONFIGURACIJA:**

### **1. Environment Variables**
```bash
# Supabase Configuration
SUPABASE_URL=https://iiuvcxvwzyottissoxks.supabase.co
SUPABASE_ANON_KEY=your_actual_anon_key_here
SUPABASE_SERVICE_KEY=your_actual_service_key_here

# Database Configuration
DATABASE_URL=postgresql://postgres.iiuvcxvwzyottissoxks:YOUR_PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

### **2. Supabase Dashboard Setup**
1. **Ustvarite tabele** v Supabase SQL Editor:

```sql
-- Create tender_listings table
CREATE TABLE tender_listings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform VARCHAR(50) NOT NULL,
    platform_id VARCHAR(255),
    title TEXT NOT NULL,
    description TEXT,
    organization VARCHAR(500),
    url TEXT,
    notice_id VARCHAR(255),
    posted_date TIMESTAMP,
    response_deadline TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    estimated_value FLOAT,
    currency VARCHAR(10),
    category VARCHAR(255),
    type VARCHAR(100),
    status VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    raw_data JSONB,
    search_query TEXT,
    search_timestamp TIMESTAMP DEFAULT NOW()
);

-- Create search_logs table
CREATE TABLE search_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform VARCHAR(50) NOT NULL,
    query_params JSONB NOT NULL,
    results_count INTEGER DEFAULT 0,
    execution_time FLOAT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_tender_listings_platform ON tender_listings(platform);
CREATE INDEX idx_tender_listings_posted_date ON tender_listings(posted_date);
CREATE INDEX idx_tender_listings_created_at ON tender_listings(created_at);
CREATE INDEX idx_search_logs_platform ON search_logs(platform);
CREATE INDEX idx_search_logs_timestamp ON search_logs(timestamp);
```

## 📊 **KAKO DELUJE:**

### **1. Avtomatsko shranjevanje**
Ko uporabnik izvede search na katerikoli platformi:
1. **API klic** se izvršuje normalno
2. **Rezultati** se vrnejo uporabniku
3. **V ozadju** se avtomatsko:
   - Shranijo tender objave v `tender_listings`
   - Zabeleži search operacija v `search_logs`
   - Dodajo metadata (execution time, itd.)

### **2. Storage kontrola**
```python
# Feature flags za kontrolo shranjevanja
ENABLE_SAM_STORAGE=true      # Shrani SAM.gov rezultate
ENABLE_TED_STORAGE=true      # Shrani TED Europe rezultate  
ENABLE_BONFIRE_STORAGE=true  # Shrani Bonfire rezultate
```

### **3. Connection types**
- **Transaction pooler** (default) - Za serverless aplikacije
- **Direct connection** - Za persistent aplikacije
- **Session pooler** - Za IPv4 kompatibilnost

## 🧪 **TESTIRANJE:**

### **1. Database Status**
```bash
GET /database/status
```
Vrne:
- Database connection status
- Supabase connection status
- Storage settings
- Statistike

### **2. Test Save**
```bash
POST /database/test-save
```
Shrani test tender v bazo za preverjanje funkcionalnosti.

### **3. View Stored Tenders**
```bash
GET /database/tenders?platform=sam&limit=10
```
Prikaže shranjene tender objave.

## 🚀 **DEPLOYMENT:**

### **1. Railway Deployment**
```bash
# Dodajte environment variables v Railway dashboard:
SUPABASE_URL=https://iiuvcxvwzyottissoxks.supabase.co
SUPABASE_ANON_KEY=your_key
DATABASE_URL=postgresql://...
```

### **2. Lokalni Development**
```bash
# Ustvarite .env datoteko
cp .env.example .env
# Uredite .env z vašimi credentials
# Zaženite server
python3 -m uvicorn main:app --reload
```

## 📈 **PERFORMANCE:**

### **Optimizacije:**
- ✅ **Async operations** - Shranjevanje ne blokira API response
- ✅ **Connection pooling** - Optimizirane database povezave
- ✅ **Batch operations** - Množično shranjevanje
- ✅ **Error handling** - Graceful failure handling
- ✅ **Indexing** - Database indeksi za hitrejše queries

### **Monitoring:**
- ✅ **Execution time tracking** - Merjenje performance
- ✅ **Success/failure logging** - Error tracking
- ✅ **Storage statistics** - Usage metrics

## 🔒 **SECURITY:**

### **Best Practices:**
- ✅ **Environment variables** - Credentials niso v kodi
- ✅ **Connection pooling** - Secure database connections
- ✅ **Input validation** - Pydantic models
- ✅ **Error handling** - No sensitive data exposure

## 📋 **NEXT STEPS:**

1. **Dodajte prave Supabase credentials**
2. **Ustvarite tabele v Supabase dashboard**
3. **Testirajte z realnimi SAM.gov searches**
4. **Deployajte na Railway**
5. **Monitorajte performance in storage usage**

**Supabase integracija je pripravljena za produkcijsko uporabo!** 🎉

