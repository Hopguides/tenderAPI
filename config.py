"""
Tender API Configuration
Includes Supabase database configuration
"""
import os
from typing import Optional

class Config:
    """Application configuration"""
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv(
        "SUPABASE_URL", 
        "https://iiuvcxvwzyottissoxks.supabase.co"
    )
    
    SUPABASE_ANON_KEY: str = os.getenv(
        "SUPABASE_ANON_KEY", 
        ""  # Will be set via environment variable
    )
    
    SUPABASE_SERVICE_KEY: str = os.getenv(
        "SUPABASE_SERVICE_KEY", 
        ""  # Will be set via environment variable
    )
    
    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres.iiuvcxvwzyottissoxks:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
    )
    
    # Direct connection (for persistent connections)
    DATABASE_DIRECT_URL: str = os.getenv(
        "DATABASE_DIRECT_URL",
        "postgresql://postgres:[YOUR-PASSWORD]@db.iiuvcxvwzyottissoxks.supabase.co:5432/postgres"
    )
    
    # Session pooler (for IPv4 compatibility)
    DATABASE_SESSION_URL: str = os.getenv(
        "DATABASE_SESSION_URL",
        "postgresql://postgres.iiuvcxvwzyottissoxks:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:5432/postgres"
    )
    
    # Application Configuration
    APP_NAME: str = "Tender API with Supabase"
    APP_VERSION: str = "2.1.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Tender API Configuration
    ENABLE_SAM_STORAGE: bool = os.getenv("ENABLE_SAM_STORAGE", "true").lower() == "true"
    ENABLE_TED_STORAGE: bool = os.getenv("ENABLE_TED_STORAGE", "true").lower() == "true"
    ENABLE_BONFIRE_STORAGE: bool = os.getenv("ENABLE_BONFIRE_STORAGE", "true").lower() == "true"
    
    @classmethod
    def get_database_url(cls, connection_type: str = "transaction") -> str:
        """
        Get database URL based on connection type
        
        Args:
            connection_type: 'direct', 'transaction', or 'session'
        
        Returns:
            Database connection string
        """
        if connection_type == "direct":
            return cls.DATABASE_DIRECT_URL
        elif connection_type == "session":
            return cls.DATABASE_SESSION_URL
        else:  # transaction (default)
            return cls.DATABASE_URL
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that required configuration is present"""
        required_vars = [
            cls.SUPABASE_URL,
            cls.SUPABASE_ANON_KEY
        ]
        
        missing_vars = [var for var in required_vars if not var]
        
        if missing_vars:
            print(f"Missing required configuration: {missing_vars}")
            return False
        
        return True

# Global config instance
config = Config()

