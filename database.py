"""
Database models and connection for Tender API
Supports Supabase PostgreSQL database
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
import uuid
import logging
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SQLAlchemy setup
Base = declarative_base()

class TenderListing(Base):
    """
    Model for storing tender listings from various platforms
    """
    __tablename__ = "tender_listings"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Platform information
    platform = Column(String(50), nullable=False, index=True)  # 'sam', 'ted', 'bonfire'
    platform_id = Column(String(255), nullable=True, index=True)  # Original ID from platform
    
    # Basic tender information
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    organization = Column(String(500), nullable=True)
    
    # URLs and references
    url = Column(Text, nullable=True)
    notice_id = Column(String(255), nullable=True, index=True)
    
    # Dates
    posted_date = Column(DateTime, nullable=True, index=True)
    response_deadline = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Financial information
    estimated_value = Column(Float, nullable=True)
    currency = Column(String(10), nullable=True)
    
    # Classification
    category = Column(String(255), nullable=True)
    type = Column(String(100), nullable=True)
    
    # Status and flags
    status = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Raw data from platform (JSON)
    raw_data = Column(JSON, nullable=True)
    
    # Search metadata
    search_query = Column(Text, nullable=True)
    search_timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<TenderListing(id={self.id}, platform={self.platform}, title={self.title[:50]}...)>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'platform': self.platform,
            'platform_id': self.platform_id,
            'title': self.title,
            'description': self.description,
            'organization': self.organization,
            'url': self.url,
            'notice_id': self.notice_id,
            'posted_date': self.posted_date.isoformat() if self.posted_date else None,
            'response_deadline': self.response_deadline.isoformat() if self.response_deadline else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'estimated_value': self.estimated_value,
            'currency': self.currency,
            'category': self.category,
            'type': self.type,
            'status': self.status,
            'is_active': self.is_active,
            'raw_data': self.raw_data,
            'search_query': self.search_query,
            'search_timestamp': self.search_timestamp.isoformat()
        }

class SearchLog(Base):
    """
    Model for logging search queries and results
    """
    __tablename__ = "search_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform = Column(String(50), nullable=False, index=True)
    query_params = Column(JSON, nullable=False)
    results_count = Column(Integer, nullable=False, default=0)
    execution_time = Column(Float, nullable=True)  # in seconds
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<SearchLog(platform={self.platform}, results={self.results_count}, timestamp={self.timestamp})>"

class DatabaseManager:
    """
    Database connection and session management
    """
    
    def __init__(self, connection_type: str = "transaction"):
        """
        Initialize database manager
        
        Args:
            connection_type: 'direct', 'transaction', or 'session'
        """
        self.connection_type = connection_type
        self.database_url = config.get_database_url(connection_type)
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize SQLAlchemy engine and session factory"""
        try:
            # Create engine with appropriate settings
            engine_kwargs = {
                'echo': config.DEBUG,
                'pool_pre_ping': True,
                'pool_recycle': 300,  # 5 minutes
            }
            
            # Adjust settings based on connection type
            if self.connection_type == "transaction":
                # For serverless/short-lived connections
                engine_kwargs.update({
                    'pool_size': 5,
                    'max_overflow': 10,
                    'pool_timeout': 30
                })
            elif self.connection_type == "direct":
                # For persistent connections
                engine_kwargs.update({
                    'pool_size': 10,
                    'max_overflow': 20,
                    'pool_timeout': 60
                })
            else:  # session
                # For IPv4 compatibility
                engine_kwargs.update({
                    'pool_size': 5,
                    'max_overflow': 10,
                    'pool_timeout': 30
                })
            
            self.engine = create_engine(self.database_url, **engine_kwargs)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            logger.info(f"Database engine initialized with {self.connection_type} connection")
            
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise
    
    def create_tables(self):
        """Create all tables in the database"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.engine.connect() as connection:
                result = connection.execute("SELECT 1")
                return result.fetchone()[0] == 1
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with self.get_session() as session:
                tender_count = session.query(TenderListing).count()
                search_count = session.query(SearchLog).count()
                
                # Platform breakdown
                platform_stats = {}
                for platform in ['sam', 'ted', 'bonfire']:
                    count = session.query(TenderListing).filter(
                        TenderListing.platform == platform
                    ).count()
                    platform_stats[platform] = count
                
                return {
                    'total_tenders': tender_count,
                    'total_searches': search_count,
                    'platform_breakdown': platform_stats,
                    'connection_type': self.connection_type
                }
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {'error': str(e)}

# Global database manager instance
db_manager = DatabaseManager()

def get_db() -> Session:
    """Dependency for getting database session"""
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize database tables"""
    try:
        db_manager.create_tables()
        logger.info("Database initialization completed")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

