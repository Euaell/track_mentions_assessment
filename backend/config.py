import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

@dataclass
class RedditConfig:
    """Reddit API configuration"""
    client_id: str
    client_secret: str
    user_agent: str
    username: str = None
    password: str = None

@dataclass
class SteamConfig:
    """Steam/SteamDB configuration"""
    base_url: str = "https://steamdb.info"
    request_delay: float = 1.0  # Seconds between requests
    user_agent: str = "SteamMentionsTracker/1.0"

@dataclass
class AppConfig:
    """Main application configuration"""
    # Reddit settings
    reddit: RedditConfig
    
    # Steam settings  
    steam: SteamConfig
    
    # Data settings
    data_dir: str = "data"
    days_to_collect: int = 30
    
    # API settings
    host: str = "localhost"
    port: int = 5000
    debug: bool = True

def load_config() -> AppConfig:
    """Load configuration from environment variables"""
    
    # Reddit credentials (required)
    reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
    reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    reddit_user_agent = os.getenv("REDDIT_USER_AGENT", "SteamMentionsTracker/1.0")
    reddit_username = os.getenv("REDDIT_USERNAME")
    reddit_password = os.getenv("REDDIT_PASSWORD")
    
    if not reddit_client_id or not reddit_client_secret:
        raise ValueError(
            "Reddit credentials not found. Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables."
        )
    
    reddit_config = RedditConfig(
        client_id=reddit_client_id,
        client_secret=reddit_client_secret,
        user_agent=reddit_user_agent,
        username=reddit_username,
        password=reddit_password
    )
    
    steam_config = SteamConfig()

    # assert the reddit credentials are not None
    if reddit_username is None or reddit_password is None:
        raise ValueError(
            "Reddit credentials not found. Please set REDDIT_USERNAME and REDDIT_PASSWORD environment variables."
        )
    
    return AppConfig(
        reddit=reddit_config,
        steam=steam_config,
        data_dir=os.getenv("DATA_DIR", "data"),
        days_to_collect=int(os.getenv("DAYS_TO_COLLECT", "30")),
        host=os.getenv("HOST", "localhost"),
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("DEBUG", "true").lower() == "true"
    )

# Global config instance
config = load_config()
