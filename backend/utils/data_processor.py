import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import logging
import csv
from pathlib import Path

from scrapers.reddit_client import RedditMention, RedditClient
from scrapers.stream_scraper import SteamFollowerData, SteamDBScraper
from config import config

logger = logging.getLogger(__name__)

class DataProcessor:
    """Process and merge Steam and Reddit data"""
    
    def __init__(self):
        """Initialize the data processor"""
        self.data_dir = Path(config.data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
    def merge_steam_reddit_data(
        self, 
        steam_data: List[SteamFollowerData], 
        reddit_mentions: List[RedditMention]
    ) -> pd.DataFrame:
        """
        Merge Steam follower data with Reddit mentions by date
        
        Args:
            steam_data: List of Steam follower data points
            reddit_mentions: List of Reddit mentions
            
        Returns:
            DataFrame with columns: date, steam_followers_count, mentions_in_social_media
        """
        logger.info("Merging Steam and Reddit data")
        
        # Convert to DataFrames
        steam_scraper = SteamDBScraper()
        reddit_client = RedditClient()
        
        steam_df = steam_scraper.get_daily_follower_counts(steam_data)
        reddit_df = reddit_client.get_daily_mention_counts(reddit_mentions)
        
        # Create date range for the analysis period
        if steam_df.empty and reddit_df.empty:
            logger.warning("No data available for merging")
            return pd.DataFrame(columns=['date', 'steam_followers_count', 'mentions_in_social_media'])
        
        # Determine date range
        start_date = None
        end_date = None
        
        if not steam_df.empty:
            steam_dates = pd.to_datetime(steam_df['date'])
            start_date = steam_dates.min()
            end_date = steam_dates.max()
        
        if not reddit_df.empty:
            reddit_dates = pd.to_datetime(reddit_df['date'])
            if start_date is None:
                start_date = reddit_dates.min()
                end_date = reddit_dates.max()
            else:
                start_date = min(start_date, reddit_dates.min())
                end_date = max(end_date, reddit_dates.max())
        
        if start_date is None:
            start_date = datetime.now().date() - timedelta(days=30)
            end_date = datetime.now().date()
        
        # Create complete date range
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        result_df = pd.DataFrame({'date': date_range.date})
        
        # Merge Steam data
        if not steam_df.empty:
            steam_df['date'] = pd.to_datetime(steam_df['date']).dt.date
            result_df = result_df.merge(
                steam_df[['date', 'steam_followers']], 
                on='date', 
                how='left'
            ).rename(columns={'steam_followers': 'steam_followers_count'})
        else:
            result_df['steam_followers_count'] = 0
        
        # Merge Reddit data
        if not reddit_df.empty:
            reddit_df['date'] = pd.to_datetime(reddit_df['date']).dt.date
            result_df = result_df.merge(
                reddit_df[['date', 'mention_count']], 
                on='date', 
                how='left'
            ).rename(columns={'mention_count': 'mentions_in_social_media'})
        else:
            result_df['mentions_in_social_media'] = 0
        
        # Fill missing values
        result_df['steam_followers_count'] = result_df['steam_followers_count'].fillna(0).astype(int)
        result_df['mentions_in_social_media'] = result_df['mentions_in_social_media'].fillna(0).astype(int)
        
        # Sort by date
        result_df = result_df.sort_values('date').reset_index(drop=True)
        
        logger.info(f"Merged data contains {len(result_df)} days")
        return result_df
    
    def export_to_csv(self, data: pd.DataFrame, filename: str = None) -> str:
        """
        Export merged data to CSV file
        
        Args:
            data: DataFrame to export
            filename: Optional filename, will generate one if not provided
            
        Returns:
            Path to the exported CSV file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"steam_reddit_comparison_{timestamp}.csv"
        
        filepath = self.data_dir / filename
        
        # Ensure proper column order and formatting
        export_df = data.copy()
        
        # Format date column
        export_df['date'] = pd.to_datetime(export_df['date']).dt.strftime('%Y-%m-%d')
        
        # Reorder columns to match requirements
        column_order = ['date', 'steam_followers_count', 'mentions_in_social_media']
        export_df = export_df[column_order]
        
        # Export to CSV
        export_df.to_csv(filepath, index=False)
        
        logger.info(f"Data exported to {filepath}")
        return str(filepath)
    
    def print_comparison_table(self, data: pd.DataFrame, max_rows: int = 50):
        """
        Print comparison table to console
        
        Args:
            data: DataFrame to print
            max_rows: Maximum number of rows to display
        """
        print("\n" + "="*60)
        print("STEAM GAME FOLLOWERS vs REDDIT MENTIONS COMPARISON")
        print("="*60)
        
        if data.empty:
            print("No data available to display.")
            return
        
        # Format the data for display
        display_df = data.copy()
        display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%Y-%m-%d')
        
        # Rename columns for display
        display_df.columns = ['Date', 'Steam Followers Count', 'Mentions in Social Media']
        
        # Limit rows if too many
        if len(display_df) > max_rows:
            print(f"Showing first {max_rows} rows (total: {len(display_df)} rows)")
            display_df = display_df.head(max_rows)
        
        # Print the table
        print(display_df.to_string(index=False))
        
        # Print summary statistics
        print("\n" + "-"*60)
        print("SUMMARY STATISTICS")
        print("-"*60)
        
        steam_data = data['steam_followers_count']
        reddit_data = data['mentions_in_social_media']
        
        print(f"Steam Followers - Min: {steam_data.min():,}, Max: {steam_data.max():,}, Avg: {steam_data.mean():.0f}")
        print(f"Reddit Mentions - Min: {reddit_data.min():,}, Max: {reddit_data.max():,}, Avg: {reddit_data.mean():.1f}")
        print(f"Total Reddit Mentions: {reddit_data.sum():,}")
        print(f"Days with Reddit Activity: {(reddit_data > 0).sum()}")
        
        # Correlation analysis
        if len(data) > 1 and steam_data.std() > 0 and reddit_data.std() > 0:
            correlation = steam_data.corr(reddit_data)
            print(f"Correlation between followers and mentions: {correlation:.3f}")
        
        print("="*60)
    
    def generate_summary_stats(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate summary statistics for the merged data
        
        Args:
            data: Merged DataFrame
            
        Returns:
            Dictionary with summary statistics
        """
        if data.empty:
            return {}
        
        steam_data = data['steam_followers_count']
        reddit_data = data['mentions_in_social_media']
        
        stats = {
            'date_range': {
                'start': data['date'].min(),
                'end': data['date'].max(),
                'total_days': len(data)
            },
            'steam_followers': {
                'min': int(steam_data.min()),
                'max': int(steam_data.max()),
                'mean': float(steam_data.mean()),
                'std': float(steam_data.std()) if len(steam_data) > 1 else 0.0,
                'change': int(steam_data.iloc[-1] - steam_data.iloc[0]) if len(steam_data) > 0 else 0
            },
            'reddit_mentions': {
                'total': int(reddit_data.sum()),
                'min': int(reddit_data.min()),
                'max': int(reddit_data.max()),
                'mean': float(reddit_data.mean()),
                'std': float(reddit_data.std()) if len(reddit_data) > 1 else 0.0,
                'active_days': int((reddit_data > 0).sum())
            }
        }
        
        # Add correlation if applicable
        if len(data) > 1 and steam_data.std() > 0 and reddit_data.std() > 0:
            stats['correlation'] = float(steam_data.corr(reddit_data))
        else:
            stats['correlation'] = None
        
        return stats
    
    def save_raw_data(self, steam_data: List[SteamFollowerData], reddit_mentions: List[RedditMention]):
        """Save raw data for future analysis"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save Steam data
        if steam_data:
            steam_df = SteamDBScraper().follower_data_to_dataframe(steam_data)
            steam_path = self.data_dir / f"steam_raw_{timestamp}.csv"
            steam_df.to_csv(steam_path, index=False)
            logger.info(f"Raw Steam data saved to {steam_path}")
        
        # Save Reddit data
        if reddit_mentions:
            reddit_df = RedditClient().mentions_to_dataframe(reddit_mentions)
            reddit_path = self.data_dir / f"reddit_raw_{timestamp}.csv"
            reddit_df.to_csv(reddit_path, index=False)
            logger.info(f"Raw Reddit data saved to {reddit_path}")
