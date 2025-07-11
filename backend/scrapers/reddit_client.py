import sys
import praw
import pandas as pd
from datetime import datetime, timedelta, UTC
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import time
import logging

from config import config

logger = logging.getLogger(__name__)

@dataclass
class RedditMention:
    """Data structure for a Reddit mention"""
    id: str
    title: str
    subreddit: str
    author: str
    created_utc: datetime
    score: int
    num_comments: int
    url: str

class RedditClient:
    """Client for collecting Reddit mentions of games"""
    
    def __init__(self):
        """Initialize Reddit client with credentials from config"""
        
        # Build Reddit client parameters
        reddit_params = {
            "client_id": config.reddit.client_id,
            "client_secret": config.reddit.client_secret,
            "user_agent": config.reddit.user_agent
        }
        
        # Add username/password if available (for script-type apps)
        if config.reddit.username and config.reddit.password:
            reddit_params["username"] = config.reddit.username
            reddit_params["password"] = config.reddit.password
            logger.info("Using username/password authentication")
        else:
            logger.info("Using read-only authentication")
        
        self.reddit = praw.Reddit(**reddit_params)
        
        # Test connection with a simple API call
        try:
            # Try to access a public subreddit (doesn't require auth)
            test_sub = self.reddit.subreddit("test")
            assert test_sub.display_name  # This will trigger an API call
            logger.info("Reddit client initialized successfully")
        except Exception as e:
            logger.error(f"Reddit client connection test failed: {e}")
            sys.exit(1)
    
    def search_game_mentions(
        self, 
        game_name: str, 
        days: int = 30,
        subreddits: Optional[List[str]] = None,
        limit: int = 1000
    ) -> List[RedditMention]:
        """
        Search for mentions of a game across Reddit
        
        Args:
            game_name: Name of the game to search for
            days: Number of days to go back
            subreddits: Specific subreddits to search (None for all)
            limit: Maximum number of posts to retrieve
            
        Returns:
            List of RedditMention objects
        """
        logger.info(f"Searching for '{game_name}' mentions over last {days} days")
        
        mentions = []
        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        
        # Search queries to try
        search_queries = [
            game_name,
            f'"{game_name}"',  # Exact phrase
            game_name.replace(" ", "")  # No spaces version
        ]
        
        # Default subreddits to search if none specified
        if subreddits is None:
            subreddits = [
                "all",  # Search all of Reddit
                "gaming",
                "Steam", 
                "pcgaming",
                "GameDeals",
                "tipofmyjoystick"
            ]
        
        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                for query in search_queries:
                    logger.info(f"Searching r/{subreddit_name} for: {query}")
                    
                    # Search submissions
                    for submission in subreddit.search(query, limit=limit, sort="new"):
                        created_date = datetime.fromtimestamp(submission.created_utc, UTC)
                        
                        # Skip if too old
                        if created_date < cutoff_date:
                            continue
                            
                        mention = RedditMention(
                            id=submission.id,
                            title=submission.title,
                            subreddit=submission.subreddit.display_name,
                            author=str(submission.author) if submission.author else "[deleted]",
                            created_utc=created_date,
                            score=submission.score,
                            num_comments=submission.num_comments,
                            url=submission.url
                        )
                        
                        mentions.append(mention)
                        
                    # Rate limiting
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error searching r/{subreddit_name}: {e}")
                continue
        
        # Remove duplicates based on post ID
        unique_mentions = {}
        for mention in mentions:
            if mention.id not in unique_mentions:
                unique_mentions[mention.id] = mention
        
        result = list(unique_mentions.values())
        logger.info(f"Found {len(result)} unique mentions")
        
        return result
    
    def mentions_to_dataframe(self, mentions: List[RedditMention]) -> pd.DataFrame:
        """Convert mentions to pandas DataFrame"""
        data = []
        for mention in mentions:
            data.append({
                'id': mention.id,
                'title': mention.title,
                'subreddit': mention.subreddit,
                'author': mention.author,
                'created_utc': mention.created_utc,
                'date': mention.created_utc.date(),
                'score': mention.score,
                'num_comments': mention.num_comments,
                'url': mention.url
            })
        
        return pd.DataFrame(data)
    
    def get_daily_mention_counts(self, mentions: List[RedditMention]) -> pd.DataFrame:
        """
        Aggregate mentions by date
        
        Returns:
            DataFrame with columns: date, mention_count, total_score, total_comments
        """
        df = self.mentions_to_dataframe(mentions)
        
        if df.empty:
            return pd.DataFrame(columns=['date', 'mention_count', 'total_score', 'total_comments'])
        
        daily_stats = df.groupby('date').agg({
            'id': 'count',
            'score': 'sum', 
            'num_comments': 'sum'
        }).reset_index()
        
        daily_stats.columns = ['date', 'mention_count', 'total_score', 'total_comments']
        
        return daily_stats
