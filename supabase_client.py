"""
Supabase client wrapper for Tender API
Provides easy interface for database operations
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from supabase import create_client, Client
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseManager:
    """
    Supabase client manager for tender data operations
    """
    
    def __init__(self):
        """Initialize Supabase client"""
        self.client: Optional[Client] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client with configuration"""
        try:
            if not config.SUPABASE_URL or not config.SUPABASE_ANON_KEY:
                logger.warning("Supabase credentials not configured")
                return
            
            self.client = create_client(
                config.SUPABASE_URL,
                config.SUPABASE_ANON_KEY
            )
            logger.info("Supabase client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.client = None
    
    def is_connected(self) -> bool:
        """Check if Supabase client is connected"""
        return self.client is not None
    
    async def save_tender_listing(self, tender_data: Dict[str, Any]) -> Optional[str]:
        """
        Save tender listing to Supabase
        
        Args:
            tender_data: Dictionary containing tender information
            
        Returns:
            Tender ID if successful, None if failed
        """
        if not self.is_connected():
            logger.error("Supabase client not connected")
            return None
        
        try:
            # Prepare data for insertion
            insert_data = {
                'platform': tender_data.get('platform'),
                'platform_id': tender_data.get('platform_id'),
                'title': tender_data.get('title'),
                'description': tender_data.get('description'),
                'organization': tender_data.get('organization'),
                'url': tender_data.get('url'),
                'notice_id': tender_data.get('notice_id'),
                'posted_date': tender_data.get('posted_date'),
                'response_deadline': tender_data.get('response_deadline'),
                'estimated_value': tender_data.get('estimated_value'),
                'currency': tender_data.get('currency'),
                'category': tender_data.get('category'),
                'type': tender_data.get('type'),
                'status': tender_data.get('status'),
                'is_active': tender_data.get('is_active', True),
                'raw_data': tender_data.get('raw_data'),
                'search_query': tender_data.get('search_query'),
                'search_timestamp': datetime.utcnow().isoformat(),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Remove None values
            insert_data = {k: v for k, v in insert_data.items() if v is not None}
            
            # Insert into Supabase
            result = self.client.table('tender_listings').insert(insert_data).execute()
            
            if result.data:
                tender_id = result.data[0].get('id')
                logger.info(f"Tender listing saved successfully: {tender_id}")
                return tender_id
            else:
                logger.error("Failed to save tender listing: No data returned")
                return None
                
        except Exception as e:
            logger.error(f"Error saving tender listing: {e}")
            return None
    
    async def save_multiple_tenders(self, tenders: List[Dict[str, Any]]) -> int:
        """
        Save multiple tender listings to Supabase
        
        Args:
            tenders: List of tender dictionaries
            
        Returns:
            Number of successfully saved tenders
        """
        if not self.is_connected():
            logger.error("Supabase client not connected")
            return 0
        
        saved_count = 0
        
        for tender in tenders:
            result = await self.save_tender_listing(tender)
            if result:
                saved_count += 1
        
        logger.info(f"Saved {saved_count}/{len(tenders)} tender listings")
        return saved_count
    
    async def log_search(self, platform: str, query_params: Dict[str, Any], 
                        results_count: int, execution_time: float = None, 
                        success: bool = True, error_message: str = None) -> Optional[str]:
        """
        Log search operation to Supabase
        
        Args:
            platform: Platform name ('sam', 'ted', 'bonfire')
            query_params: Search parameters used
            results_count: Number of results returned
            execution_time: Time taken for search in seconds
            success: Whether search was successful
            error_message: Error message if search failed
            
        Returns:
            Log ID if successful, None if failed
        """
        if not self.is_connected():
            logger.error("Supabase client not connected")
            return None
        
        try:
            log_data = {
                'platform': platform,
                'query_params': query_params,
                'results_count': results_count,
                'execution_time': execution_time,
                'success': success,
                'error_message': error_message,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            result = self.client.table('search_logs').insert(log_data).execute()
            
            if result.data:
                log_id = result.data[0].get('id')
                logger.info(f"Search logged successfully: {log_id}")
                return log_id
            else:
                logger.error("Failed to log search: No data returned")
                return None
                
        except Exception as e:
            logger.error(f"Error logging search: {e}")
            return None
    
    async def get_tender_stats(self) -> Dict[str, Any]:
        """
        Get tender statistics from Supabase
        
        Returns:
            Dictionary with statistics
        """
        if not self.is_connected():
            return {'error': 'Supabase client not connected'}
        
        try:
            # Get total count
            total_result = self.client.table('tender_listings').select('id', count='exact').execute()
            total_count = total_result.count if total_result.count is not None else 0
            
            # Get platform breakdown
            platform_stats = {}
            for platform in ['sam', 'ted', 'bonfire']:
                platform_result = self.client.table('tender_listings').select(
                    'id', count='exact'
                ).eq('platform', platform).execute()
                platform_stats[platform] = platform_result.count if platform_result.count is not None else 0
            
            # Get recent activity (last 24 hours)
            yesterday = (datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)).isoformat()
            recent_result = self.client.table('tender_listings').select(
                'id', count='exact'
            ).gte('created_at', yesterday).execute()
            recent_count = recent_result.count if recent_result.count is not None else 0
            
            return {
                'total_tenders': total_count,
                'platform_breakdown': platform_stats,
                'recent_24h': recent_count,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting tender stats: {e}")
            return {'error': str(e)}
    
    async def search_tenders(self, platform: str = None, limit: int = 50, 
                           offset: int = 0) -> List[Dict[str, Any]]:
        """
        Search tenders in Supabase
        
        Args:
            platform: Filter by platform ('sam', 'ted', 'bonfire')
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of tender dictionaries
        """
        if not self.is_connected():
            logger.error("Supabase client not connected")
            return []
        
        try:
            query = self.client.table('tender_listings').select('*')
            
            if platform:
                query = query.eq('platform', platform)
            
            query = query.order('created_at', desc=True).limit(limit).offset(offset)
            
            result = query.execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error searching tenders: {e}")
            return []
    
    async def create_tables(self) -> bool:
        """
        Create tables in Supabase (if they don't exist)
        Note: This requires service key permissions
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Supabase client not connected")
            return False
        
        try:
            # Note: Table creation is typically done via Supabase dashboard or migrations
            # This is a placeholder for programmatic table creation
            logger.info("Tables should be created via Supabase dashboard or SQL migrations")
            return True
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            return False

# Global Supabase manager instance
supabase_manager = SupabaseManager()

def get_supabase() -> SupabaseManager:
    """Get Supabase manager instance"""
    return supabase_manager

