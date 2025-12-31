"""
Configuration for LinkedIn EJPT Scraper
"""

class Config:
    # LinkedIn URLs
    BASE_URL = "https://www.linkedin.com"
    LOGIN_URL = f"{BASE_URL}/login"
    SEARCH_URL = f"{BASE_URL}/search/results/people/"
    
    # Search Parameters
    KEYWORDS = [
        "ejpt certification",
        "ejpt certified",
        "eLearnSecurity Junior Penetration Tester",
        "INe junior penetration tester"
    ]
    
    # Scraping Limits
    MAX_PAGES = 100
    MAX_PROFILES_PER_PAGE = 10
    MAX_TOTAL_PROFILES = 1000
    
    # Delays (in seconds)
    MIN_DELAY = 2
    MAX_DELAY = 5
    PAGE_LOAD_DELAY = 3
    
    # Output Files
    OUTPUT_DIR = "data"
    RAW_DATA_FILE = "raw_profiles.json"
    PROCESSED_DATA_FILE = "ejpt_analysis.csv"
    LOG_FILE = "scraper.log"
    
    # Browser Settings
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    ]
    
    @staticmethod
    def get_search_url(keyword):
        """Generate search URL for a keyword"""
        return f"{Config.SEARCH_URL}?keywords={keyword.replace(' ', '%20')}"
