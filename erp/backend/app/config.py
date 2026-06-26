from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "ComplianceERP"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production-use-strong-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours

    # Database
    DATABASE_URL: str = "postgresql://erp_user:erp_password@localhost:5432/erp_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Sanctions APIs (free/public)
    OFAC_SDN_URL: str = "https://www.treasury.gov/ofac/downloads/sdn.xml"
    OFAC_CONSOLIDATED_URL: str = "https://www.treasury.gov/ofac/downloads/consolidated/consolidated.xml"
    # UK moved to single UKSL list Jan 28 2026 (FCDO replaced OFSI consolidated list)
    UK_SANCTIONS_URL: str = "https://assets.publishing.service.gov.uk/media/uk-sanctions-list.xml"
    UK_SANCTIONS_SEARCH_URL: str = "https://search-uk-sanctions-list.service.gov.uk/"
    UN_SANCTIONS_URL: str = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
    EU_SANCTIONS_URL: str = "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content"
    CANADA_SANCTIONS_URL: str = "https://www.international.gc.ca/world-monde/assets/office_docs/international_relations-relations_internationales/sanctions/sema-lmes.xml"
    BIS_DPL_URL: str = "https://www.bis.doc.gov/dpl/dpl.txt"
    # OpenSanctions (free for non-commercial, best consolidated source)
    OPENSANCTIONS_API_URL: str = "https://api.opensanctions.org"
    OPENSANCTIONS_API_KEY: str = ""  # Optional: set in .env for commercial use
    # Regulatory feeds
    SEC_EDGAR_API_URL: str = "https://data.sec.gov"
    FINRA_RSS_URL: str = "https://www.finra.org/sites/default/files/sub-nav/rss-news.xml"

    # Scheduler
    SANCTIONS_UPDATE_HOUR: int = 6  # 6 AM daily update

    # Jurisdictions
    SUPPORTED_JURISDICTIONS: list[str] = ["US", "UK", "CA"]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
