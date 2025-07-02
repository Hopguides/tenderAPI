from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional, List
import asyncio
import os
import time
import logging
from datetime import datetime
from base.models import TenderResponse
from platforms import get_platform, get_all_platforms, REGISTERED_PLATFORMS

# Supabase integration
from config import config
from database import init_database, get_db, db_manager
from supabase_client import get_supabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Modular Tender API with Supabase",
    description="Scalable multi-platform tender search API with Supabase database integration",
    version="2.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and Supabase on startup"""
    try:
        # Initialize database tables
        init_database()
        logger.info("Database initialized successfully")
        
        # Test Supabase connection
        supabase = get_supabase()
        if supabase.is_connected():
            logger.info("Supabase client connected successfully")
        else:
            logger.warning("Supabase client not connected - check configuration")
            
    except Exception as e:
        logger.error(f"Startup initialization failed: {e}")

# Mount static files for testing interface
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Helper function for saving tender results
async def save_tender_results(platform_name: str, search_params: Dict[str, Any], 
                            results: TenderResponse, execution_time: float = None):
    """
    Save tender search results to Supabase database
    
    Args:
        platform_name: Name of the platform searched
        search_params: Parameters used for search
        results: Search results from platform
        execution_time: Time taken for search in seconds
    """
    try:
        supabase = get_supabase()
        
        if not supabase.is_connected():
            logger.warning("Supabase not connected - skipping result storage")
            return
        
        # Log the search operation
        await supabase.log_search(
            platform=platform_name,
            query_params=search_params,
            results_count=results.total_count,
            execution_time=execution_time,
            success=True
        )
        
        # Save individual tender listings (only for enabled platforms)
        storage_enabled = {
            'sam': config.ENABLE_SAM_STORAGE,
            'ted': config.ENABLE_TED_STORAGE,
            'bonfire': config.ENABLE_BONFIRE_STORAGE
        }
        
        if storage_enabled.get(platform_name, False) and results.tenders:
            tender_data_list = []
            
            for tender in results.tenders:
                tender_data = {
                    'platform': platform_name,
                    'platform_id': getattr(tender, 'id', None),
                    'title': tender.title,
                    'description': tender.description,
                    'organization': tender.organization,
                    'url': tender.url,
                    'notice_id': getattr(tender, 'notice_id', None),
                    'posted_date': tender.posted_date.isoformat() if tender.posted_date else None,
                    'response_deadline': tender.response_deadline.isoformat() if tender.response_deadline else None,
                    'estimated_value': getattr(tender, 'estimated_value', None),
                    'currency': getattr(tender, 'currency', None),
                    'category': getattr(tender, 'category', None),
                    'type': getattr(tender, 'type', None),
                    'status': getattr(tender, 'status', None),
                    'raw_data': tender.__dict__,  # Store full tender object as JSON
                    'search_query': str(search_params)
                }
                tender_data_list.append(tender_data)
            
            # Save tenders to database
            saved_count = await supabase.save_multiple_tenders(tender_data_list)
            logger.info(f"Saved {saved_count}/{len(tender_data_list)} tenders from {platform_name}")
        
    except Exception as e:
        logger.error(f"Error saving tender results for {platform_name}: {e}")
        
        # Log failed search
        try:
            supabase = get_supabase()
            if supabase.is_connected():
                await supabase.log_search(
                    platform=platform_name,
                    query_params=search_params,
                    results_count=0,
                    execution_time=execution_time,
                    success=False,
                    error_message=str(e)
                )
        except:
            pass  # Don't fail the main request if logging fails

@app.get("/")
async def testing_interface():
    """Serve the testing interface"""
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    else:
        # Fallback to API info if no testing interface
        return await api_info()

@app.get("/api")
async def api_info():
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
            "/docs": "API documentation",
            "/": "Testing interface"
        }
    }

@app.get("/platforms")
async def get_platforms_info():
    """Get information about all registered platforms"""
    platforms_list = []
    
    for name, platform_class in REGISTERED_PLATFORMS.items():
        try:
            instance = platform_class()
            auth_req = instance.get_auth_requirements()
            
            # Determine status
            status = "healthy"
            if auth_req.get("required"):
                import os
                env_var = auth_req.get("env_var")
                if env_var and os.getenv(env_var, "").startswith("YOUR_"):
                    status = "needs_configuration"
            
            platforms_list.append({
                "name": name,
                "display_name": instance.platform_name,
                "base_url": instance.base_url,
                "status": status,
                "auth_requirements": auth_req,
                "search_params": instance.get_search_params_schema()
            })
            
        except Exception as e:
            platforms_list.append({
                "name": name,
                "display_name": name.upper(),
                "base_url": "unknown",
                "status": "error",
                "error": str(e)
            })
    
    return {
        "platforms": platforms_list,
        "total": len(platforms_list)
    }

@app.post("/search/{platform_name}")
async def search_platform(platform_name: str, search_params: Dict[str, Any]):
    """Dynamic endpoint for any registered platform with automatic result storage"""
    start_time = time.time()
    
    try:
        platform = get_platform(platform_name)
        result = await platform.search(**search_params)
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Save results to Supabase (async, don't block response)
        asyncio.create_task(save_tender_results(
            platform_name=platform_name,
            search_params=search_params,
            results=result,
            execution_time=execution_time
        ))
        
        # Add metadata to response
        result.metadata = getattr(result, 'metadata', {})
        result.metadata.update({
            'execution_time': round(execution_time, 3),
            'storage_enabled': {
                'sam': config.ENABLE_SAM_STORAGE,
                'ted': config.ENABLE_TED_STORAGE,
                'bonfire': config.ENABLE_BONFIRE_STORAGE
            }.get(platform_name, False),
            'supabase_connected': get_supabase().is_connected()
        })
        
        return result
        
    except ValueError as e:
        # Log failed search
        execution_time = time.time() - start_time
        asyncio.create_task(save_tender_results(
            platform_name=platform_name,
            search_params=search_params,
            results=TenderResponse(tenders=[], total_count=0, platform=platform_name),
            execution_time=execution_time
        ))
        raise HTTPException(status_code=404, detail=str(e))
        
    except Exception as e:
        # Log failed search
        execution_time = time.time() - start_time
        asyncio.create_task(save_tender_results(
            platform_name=platform_name,
            search_params=search_params,
            results=TenderResponse(tenders=[], total_count=0, platform=platform_name),
            execution_time=execution_time
        ))
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

# Supabase Testing and Database Endpoints
@app.get("/database/status")
async def database_status():
    """Get database connection status and statistics"""
    try:
        # Test database connection
        db_connected = db_manager.test_connection()
        
        # Test Supabase connection
        supabase = get_supabase()
        supabase_connected = supabase.is_connected()
        
        # Get database statistics
        db_stats = db_manager.get_stats()
        
        # Get Supabase statistics
        supabase_stats = await supabase.get_tender_stats() if supabase_connected else {}
        
        return {
            "database": {
                "connected": db_connected,
                "connection_type": db_manager.connection_type,
                "statistics": db_stats
            },
            "supabase": {
                "connected": supabase_connected,
                "url": config.SUPABASE_URL,
                "statistics": supabase_stats
            },
            "storage_settings": {
                "sam_storage": config.ENABLE_SAM_STORAGE,
                "ted_storage": config.ENABLE_TED_STORAGE,
                "bonfire_storage": config.ENABLE_BONFIRE_STORAGE
            }
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "database": {"connected": False},
            "supabase": {"connected": False}
        }

@app.get("/database/tenders")
async def get_stored_tenders(
    platform: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get stored tender listings from Supabase"""
    try:
        supabase = get_supabase()
        
        if not supabase.is_connected():
            raise HTTPException(status_code=503, detail="Supabase not connected")
        
        tenders = await supabase.search_tenders(
            platform=platform,
            limit=limit,
            offset=offset
        )
        
        return {
            "tenders": tenders,
            "count": len(tenders),
            "platform_filter": platform,
            "pagination": {
                "limit": limit,
                "offset": offset
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/database/test-save")
async def test_save_tender():
    """Test saving a sample tender to Supabase"""
    try:
        supabase = get_supabase()
        
        if not supabase.is_connected():
            raise HTTPException(status_code=503, detail="Supabase not connected")
        
        # Create test tender data
        test_tender = {
            'platform': 'test',
            'platform_id': 'TEST-001',
            'title': 'Test Tender - Supabase Integration',
            'description': 'This is a test tender to verify Supabase integration is working correctly.',
            'organization': 'Test Organization',
            'url': 'https://example.com/test-tender',
            'notice_id': 'TEST-NOTICE-001',
            'posted_date': datetime.utcnow().isoformat(),
            'estimated_value': 50000.0,
            'currency': 'USD',
            'category': 'Testing',
            'type': 'Test',
            'status': 'Active',
            'search_query': 'test=true'
        }
        
        # Save to Supabase
        tender_id = await supabase.save_tender_listing(test_tender)
        
        if tender_id:
            return {
                "success": True,
                "message": "Test tender saved successfully",
                "tender_id": tender_id,
                "test_data": test_tender
            }
        else:
            return {
                "success": False,
                "message": "Failed to save test tender"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/database/test-data")
async def cleanup_test_data():
    """Clean up test data from database"""
    try:
        supabase = get_supabase()
        
        if not supabase.is_connected():
            raise HTTPException(status_code=503, detail="Supabase not connected")
        
        # Note: This would require additional implementation in supabase_client.py
        # For now, return a message
        return {
            "message": "Test data cleanup would be implemented here",
            "note": "Use Supabase dashboard to manually delete test records with platform='test'"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/database/search-logs")
async def get_search_logs(limit: int = 50):
    """Get recent search logs from database"""
    try:
        # This would require additional implementation
        # For now, return placeholder
        return {
            "message": "Search logs endpoint - implementation pending",
            "note": "Would show recent search operations and their results"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)