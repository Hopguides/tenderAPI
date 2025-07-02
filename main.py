from fastapi import FastAPI, HTTPException
from typing import Dict, Any, Optional
import asyncio
from base.models import TenderResponse
from platforms import get_platform, get_all_platforms, REGISTERED_PLATFORMS

app = FastAPI(
    title="Modular Tender API",
    description="Scalable multi-platform tender search API",
    version="2.0.0"
)

@app.get("/")
async def root():
    """API info with auto-discovered platforms"""
    platforms = list(REGISTERED_PLATFORMS.keys())
    return {
        "name": "Modular Tender API",
        "version": "2.0.0",
        "platforms": platforms,
        "endpoints": {
            f"/search/{platform}": f"Search {platform} platform" 
            for platform in platforms
        } | {
            "/search/all": "Search all platforms",
            "/platforms": "Platform information",
            "/docs": "API documentation"
        }
    }

@app.get("/platforms")
async def get_platforms_info():
    """Get information about all registered platforms"""
    platforms_info = {}
    
    for name, platform_class in REGISTERED_PLATFORMS.items():
        instance = platform_class()
        platforms_info[name] = {
            "name": instance.platform_name,
            "base_url": instance.base_url,
            "auth_requirements": instance.get_auth_requirements(),
            "search_params": instance.get_search_params_schema()
        }
    
    return platforms_info

@app.post("/search/{platform_name}")
async def search_platform(platform_name: str, search_params: Dict[str, Any]):
    """Dynamic endpoint for any registered platform"""
    try:
        platform = get_platform(platform_name)
        result = await platform.search(**search_params)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search/all")
async def search_all_platforms(search_requests: Dict[str, Dict[str, Any]]):
    """Search multiple platforms simultaneously"""
    
    if not search_requests:
        raise HTTPException(status_code=400, detail="No search requests provided")
    
    # Prepare tasks
    tasks = []
    for platform_name, params in search_requests.items():
        if platform_name not in REGISTERED_PLATFORMS:
            continue
        
        try:
            platform = get_platform(platform_name)
            tasks.append((platform_name, platform.search(**params)))
        except Exception as e:
            # Skip problematic platforms
            continue
    
    if not tasks:
        raise HTTPException(status_code=400, detail="No valid search requests")
    
    # Execute concurrently
    results = {}
    completed_tasks = await asyncio.gather(
        *[task[1] for task in tasks], 
        return_exceptions=True
    )
    
    for i, (platform_name, _) in enumerate(tasks):
        result = completed_tasks[i]
        if isinstance(result, Exception):
            results[platform_name] = {
                "error": str(result),
                "platform": platform_name,
                "status": "error"
            }
        else:
            results[platform_name] = result
    
    return {
        "search_results": results,
        "summary": {
            "platforms_searched": len(tasks),
            "successful": len([r for r in completed_tasks if not isinstance(r, Exception)]),
            "total_results": sum([
                r.total_count for r in completed_tasks 
                if not isinstance(r, Exception)
            ])
        }
    }

@app.get("/health")
async def health_check():
    """Health check for all platforms"""
    platform_status = {}
    
    for name, platform_class in REGISTERED_PLATFORMS.items():
        try:
            instance = platform_class()
            auth_req = instance.get_auth_requirements()
            
            if auth_req.get("required"):
                # Check if auth is configured
                import os
                env_var = auth_req.get("env_var")
                if env_var and os.getenv(env_var, "").startswith("YOUR_"):
                    platform_status[name] = "needs_configuration"
                else:
                    platform_status[name] = "configured"
            else:
                platform_status[name] = "available"
                
        except Exception as e:
            platform_status[name] = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "platforms": platform_status,
        "registered_platforms": len(REGISTERED_PLATFORMS)
    }

# Quick search endpoints for convenience
@app.get("/quick/ted")
async def quick_ted_search(
    query: Optional[str] = None,
    country: Optional[str] = None,
    limit: int = 10
):
    """Quick TED search with GET params"""
    platform = get_platform("ted")
    return await platform.search(query=query, country=country, limit=limit)

@app.get("/quick/sam")
async def quick_sam_search(
    posted_from: str,
    posted_to: str,
    dept_name: Optional[str] = None,
    limit: int = 10
):
    """Quick SAM search with GET params"""
    platform = get_platform("sam")
    return await platform.search(
        posted_from=posted_from,
        posted_to=posted_to,
        dept_name=dept_name,
        limit=limit
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)