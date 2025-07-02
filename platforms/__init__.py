import importlib
import pkgutil
from typing import Dict, Type
from base.platform import BasePlatform

# Auto-discovery of platforms
REGISTERED_PLATFORMS: Dict[str, Type[BasePlatform]] = {}

def register_platform(name: str, platform_class: Type[BasePlatform]):
    """Register a platform class"""
    REGISTERED_PLATFORMS[name] = platform_class

def get_platform(name: str, config: Dict = None) -> BasePlatform:
    """Get platform instance by name"""
    if name not in REGISTERED_PLATFORMS:
        raise ValueError(f"Platform {name} not found. Available: {list(REGISTERED_PLATFORMS.keys())}")
    return REGISTERED_PLATFORMS[name](config)

def get_all_platforms() -> Dict[str, Type[BasePlatform]]:
    """Get all registered platforms"""
    return REGISTERED_PLATFORMS.copy()

# Auto-discover and import all platform modules
def _discover_platforms():
    """Automatically discover all platform modules"""
    import platforms
    for importer, modname, ispkg in pkgutil.iter_modules(platforms.__path__, platforms.__name__ + "."):
        if not ispkg and modname != __name__:
            importlib.import_module(modname)

_discover_platforms()
