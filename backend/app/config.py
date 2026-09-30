import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)
    
    PROJECT_NAME: str = "TerraSentinel"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "app" / "data"
    FIXTURES_DIR: Path = DATA_DIR / "fixtures"
    STORAGE_DIR: Path = BASE_DIR / "storage"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/terrasentinel.db")
    
    # STAC Endpoints
    EARTH_SEARCH_STAC_URL: str = "https://earth-search.aws.element84.com/v1"
    PLANETARY_COMPUTER_STAC_URL: str = "https://planetarycomputer.microsoft.com/api/stac/v1"
    
    # Operational Thresholds
    SAR_VV_WATER_THRESHOLD_DB: float = -16.0
    SAR_VH_WATER_THRESHOLD_DB: float = -23.0
    OPTICAL_MNDWI_WATER_THRESHOLD: float = 0.0
    DEM_MAX_WATER_SLOPE_DEG: float = 8.0
    
    # Passability Thresholds
    PASSABILITY_PARTIAL_THRESHOLD: float = 0.10  # 10% overlap
    PASSABILITY_LIKELY_BLOCKED_THRESHOLD: float = 0.35  # 35% overlap
    PASSABILITY_BLOCKED_THRESHOLD: float = 0.60  # 60% overlap
    
    # Evidence Conflict Threshold
    EVIDENCE_CONFLICT_THRESHOLD: float = 0.40
    
    # Default Fixture Mode
    ALLOW_FIXTURE_FALLBACK: bool = True

settings = Settings()

# Ensure directories exist
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
