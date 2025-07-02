# Modular Tender API System

🚀 **Plugin-based tender data collection system with auto-discovery**

## 🎯 **Main Point**
Modular structure with plugin system - each platform = 1 file, easy adding new platforms, big picture ready.

## 📁 **Structure**
```
tender_api/
├── main.py              # FastAPI server
├── base/
│   ├── __init__.py      
│   ├── platform.py      # ABC base class
│   └── models.py        # Shared models
├── platforms/
│   ├── __init__.py      # Auto-discovery
│   ├── ted.py           # TED implementation
│   ├── sam.py           # SAM implementation
│   └── bonfire.py       # Add in 2 minutes
└── requirements.txt
```

## ⚡ **How to Add New Platform (2 Minutes)**

### Step 1: Create `platforms/bonfire.py`
```python
from base.platform import BasePlatform
from platforms import register_platform

class BonfirePlatform(BasePlatform):
    def get_platform_name(self) -> str:
        return "Bonfire"
    
    def get_base_url(self) -> str:
        return "https://gobonfire.com"
    
    async def search(self, organization: str, **kwargs):
        # Copy your Bonfire logic here
        return TenderResponse(...)

register_platform("bonfire", BonfirePlatform)
```

### Step 2: DONE! 🎉
- Auto-discovery finds it automatically
- `/search/bonfire` endpoint automatically exists
- `/search/all` automatically includes Bonfire

## 🎯 **Big Picture Advantages**
- ✅ Add platform = 1 file
- ✅ Zero main.py changes = Auto-discovery
- ✅ Standard interface = All platforms work the same
- ✅ Easy testing = Each platform separate
- ✅ Plugin ready = Can load from external packages

## 🚀 **Quick Start**

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the server:**
```bash
uvicorn main:app --reload
```

3. **Test endpoints:**
```bash
# Search specific platform
curl "http://localhost:8000/search/ted?organization=EU"

# Search all platforms
curl "http://localhost:8000/search/all?organization=EU"

# List available platforms
curl "http://localhost:8000/platforms"
```

## 📊 **API Endpoints**

### Auto-generated endpoints:
- `GET /platforms` - List all available platforms
- `GET /search/{platform}` - Search specific platform
- `GET /search/all` - Search all platforms
- `GET /health` - System health check

### Platform-specific endpoints:
- `GET /search/ted` - Search TED (Tenders Electronic Daily)
- `GET /search/sam` - Search SAM.gov
- `GET /search/bonfire` - Search Bonfire (when implemented)

## 🔧 **Configuration**

Environment variables:
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/tenders

# Platform API keys
TED_API_KEY=your_ted_key
SAM_API_KEY=your_sam_key
BONFIRE_API_KEY=your_bonfire_key

# Optional: Redis for caching
REDIS_URL=redis://localhost:6379
```

## 🧪 **Testing**

```bash
# Run all tests
pytest

# Test specific platform
pytest tests/test_platforms/test_ted.py

# Test auto-discovery
pytest tests/test_discovery.py
```

## 📈 **Next Steps**

1. Test TED and SAM with new structure
2. When working → copy-paste Bonfire to new file
3. Repeat for DemandStar, MyFlorida
4. Add database persistence
5. Add caching layer
6. Add monitoring and metrics

## 🎨 **Architecture**

The system uses:
- **Abstract Base Class** for platform standardization
- **Auto-discovery** for zero-config plugin loading
- **FastAPI** for automatic API documentation
- **Pydantic** for data validation
- **SQLAlchemy** for database persistence (optional)
- **Redis** for caching (optional)

**Important**: Structure is big-picture ready, but currently simple for quick testing!

