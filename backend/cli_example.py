#!/usr/bin/env python3
"""
Command-line example for the Steam Game Tracker

This script demonstrates how to use the backend components directly
without the web interface.

Usage:
    python cli_example.py "Cyberpunk 2077" 30
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from scrapers.reddit_client import RedditClient
from scrapers.stream_scraper import SteamDBScraper
from utils.data_processor import DataProcessor

def main():
    """Main CLI function"""
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python cli_example.py 'Game Name' [days]")
        print("Example: python cli_example.py 'Cyberpunk 2077' 30")
        sys.exit(1)
    
    game_name = sys.argv[1]
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    print(f"🎮 Analyzing '{game_name}' for the last {days} days")
    print("=" * 60)
    
    # Initialize components
    data_processor = DataProcessor()
    
    # Initialize Reddit client
    try:
        reddit_client = RedditClient()
        print("✅ Reddit client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Reddit client: {e}")
        print("   Please check your Reddit API credentials in .env file")
        reddit_client = None
    
    # Initialize Steam scraper
    try:
        steam_scraper = SteamDBScraper()
        print("✅ Steam scraper initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Steam scraper: {e}")
        steam_scraper = None
    
    print()
    
    # Search for the game on Steam
    steam_data = []
    app_id = None
    
    if steam_scraper:
        print(f"🔍 Searching for '{game_name}' on SteamDB...")
        search_result = steam_scraper.search_game_by_name(game_name)
        
        if search_result:
            app_id, exact_name = search_result
            print(f"   Found: {exact_name} (App ID: {app_id})")
            
            print(f"📊 Collecting Steam follower data...")
            steam_data = steam_scraper.get_follower_history(app_id, days)
            print(f"   Collected {len(steam_data)} data points")
        else:
            print(f"   ❌ Game '{game_name}' not found on SteamDB")
    
    print()
    
    # Collect Reddit mentions
    reddit_mentions = []
    
    if reddit_client:
        print(f"🔍 Searching Reddit for mentions of '{game_name}'...")
        reddit_mentions = reddit_client.search_game_mentions(game_name, days)
        print(f"   Found {len(reddit_mentions)} Reddit mentions")
    
    print()
    
    # Process and merge data
    print("🔄 Processing and merging data...")
    merged_data = data_processor.merge_steam_reddit_data(steam_data, reddit_mentions)
    
    if merged_data.empty:
        print("❌ No data available for analysis")
        return
    
    print(f"   Generated {len(merged_data)} daily data points")
    print()
    
    # Display results
    print("📋 ANALYSIS RESULTS")
    print("=" * 60)
    
    # Generate and display statistics
    stats = data_processor.generate_summary_stats(merged_data)
    
    if stats:
        print(f"📅 Analysis Period: {stats['date_range']['start']} to {stats['date_range']['end']}")
        print(f"   Total Days: {stats['date_range']['total_days']}")
        print()
        
        print("🎯 Steam Followers:")
        print(f"   Current: {stats['steam_followers']['max']:,}")
        print(f"   Range: {stats['steam_followers']['min']:,} - {stats['steam_followers']['max']:,}")
        print(f"   Average: {stats['steam_followers']['mean']:.0f}")
        print(f"   Change: {stats['steam_followers']['change']:+,}")
        print()
        
        print("💬 Reddit Mentions:")
        print(f"   Total Mentions: {stats['reddit_mentions']['total']:,}")
        print(f"   Active Days: {stats['reddit_mentions']['active_days']}")
        print(f"   Average per Day: {stats['reddit_mentions']['mean']:.1f}")
        print(f"   Peak Day: {stats['reddit_mentions']['max']} mentions")
        print()
        
        if stats['correlation'] is not None:
            correlation_pct = stats['correlation'] * 100
            print(f"📈 Correlation: {correlation_pct:.1f}%")
            if abs(correlation_pct) > 50:
                print("   Strong correlation between followers and mentions!")
            elif abs(correlation_pct) > 25:
                print("   Moderate correlation between followers and mentions")
            else:
                print("   Weak correlation between followers and mentions")
        else:
            print("📈 Correlation: Unable to calculate (insufficient data variation)")
    
    print()
    
    # Display data table
    data_processor.print_comparison_table(merged_data, max_rows=20)
    
    # Export CSV
    csv_path = data_processor.export_to_csv(merged_data, f"{game_name.lower().replace(' ', '_')}_analysis.csv")
    print(f"\n💾 Data exported to: {csv_path}")
    
    # Save raw data
    data_processor.save_raw_data(steam_data, reddit_mentions)
    print("💾 Raw data saved for future analysis")

if __name__ == "__main__":
    main() 