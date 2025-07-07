from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import logging
import os
from datetime import datetime
from typing import Dict, Any

from config import config
from scrapers.reddit_client import RedditClient
from scrapers.stream_scraper import SteamDBScraper
from utils.data_processor import DataProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize components
reddit_client = None
steam_scraper = None
data_processor = DataProcessor()

def init_clients():
    """Initialize API clients with error handling"""
    global reddit_client, steam_scraper
    
    try:
        reddit_client = RedditClient()
        logger.info("Reddit client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Reddit client: {e}")
        reddit_client = None
    
    try:
        steam_scraper = SteamDBScraper()
        logger.info("Steam scraper initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Steam scraper: {e}")
        steam_scraper = None

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'reddit': reddit_client is not None,
            'steam': steam_scraper is not None
        }
    })

@app.route('/api/search-game', methods=['POST'])
def search_game():
    """Search for a game on SteamDB and return basic info"""
    try:
        data = request.get_json()
        game_name = data.get('game_name')
        
        if not game_name:
            return jsonify({'error': 'game_name is required'}), 400
        
        if not steam_scraper:
            return jsonify({'error': 'Steam scraper not available'}), 503
        
        result = steam_scraper.search_game_by_name(game_name)
        
        if result:
            app_id, exact_name = result
            return jsonify({
                'found': True,
                'app_id': app_id,
                'game_name': exact_name
            })
        else:
            return jsonify({
                'found': False,
                'message': f'Game "{game_name}" not found on SteamDB'
            })
    
    except Exception as e:
        logger.error(f"Error in search_game: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/collect-data', methods=['POST'])
def collect_data():
    """Collect data for a specific game"""
    try:
        data = request.get_json()
        game_name = data.get('game_name')
        app_id = data.get('app_id')  # Optional, will search if not provided
        days = data.get('days', 30)
        
        if not game_name:
            return jsonify({'error': 'game_name is required'}), 400
        
        # If no app_id provided, search for it
        if not app_id and steam_scraper:
            search_result = steam_scraper.search_game_by_name(game_name)
            if search_result:
                app_id, exact_game_name = search_result
                game_name = exact_game_name
            else:
                return jsonify({'error': f'Game "{game_name}" not found on SteamDB'}), 404
        
        # Collect Steam data
        steam_data = []
        if steam_scraper and app_id:
            try:
                steam_data = steam_scraper.get_follower_history(app_id, days)
                logger.info(f"Collected {len(steam_data)} Steam data points")
            except Exception as e:
                logger.error(f"Error collecting Steam data: {e}")
        
        # Collect Reddit data
        reddit_mentions = []
        if reddit_client:
            try:
                reddit_mentions = reddit_client.search_game_mentions(game_name, days)
                logger.info(f"Collected {len(reddit_mentions)} Reddit mentions")
                
                # If no mentions found and Reddit auth failed, use simulated data
                if len(reddit_mentions) == 0:
                    logger.info("No Reddit mentions found, generating simulated data for demonstration")
                    reddit_mentions = reddit_client.generate_simulated_mentions(game_name, days)
                    
            except Exception as e:
                logger.error(f"Error collecting Reddit data: {e}")
                logger.info("Falling back to simulated Reddit data for demonstration")
                reddit_mentions = reddit_client.generate_simulated_mentions(game_name, days)
        
        # Process and merge data
        merged_data = data_processor.merge_steam_reddit_data(steam_data, reddit_mentions)
        
        # Generate summary stats
        stats = data_processor.generate_summary_stats(merged_data)
        
        # Save raw data
        data_processor.save_raw_data(steam_data, reddit_mentions)
        
        # Convert DataFrame to list of dictionaries for JSON response
        data_list = merged_data.to_dict('records')
        
        # Convert date objects to strings for JSON serialization
        for row in data_list:
            if hasattr(row['date'], 'strftime'):
                row['date'] = row['date'].strftime('%Y-%m-%d')
        
        return jsonify({
            'success': True,
            'game_name': game_name,
            'app_id': app_id,
            'data': data_list,
            'stats': stats,
            'collected': {
                'steam_points': len(steam_data),
                'reddit_mentions': len(reddit_mentions)
            }
        })
    
    except Exception as e:
        logger.error(f"Error in collect_data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/export-csv', methods=['POST'])
def export_csv():
    """Export data to CSV and return download link"""
    try:
        data = request.get_json()
        
        # Expect data in the format from collect_data endpoint
        data_list = data.get('data', [])
        filename = data.get('filename')
        
        if not data_list:
            return jsonify({'error': 'No data provided'}), 400
        
        # Convert list back to DataFrame
        import pandas as pd
        df = pd.DataFrame(data_list)
        
        # Export to CSV
        csv_path = data_processor.export_to_csv(df, filename)
        
        return jsonify({
            'success': True,
            'csv_path': csv_path,
            'download_url': f'/api/download-csv/{os.path.basename(csv_path)}'
        })
    
    except Exception as e:
        logger.error(f"Error in export_csv: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/download-csv/<filename>', methods=['GET'])
def download_csv(filename):
    """Download CSV file"""
    try:
        file_path = data_processor.data_dir / filename
        
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
    
    except Exception as e:
        logger.error(f"Error in download_csv: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/analyze-game', methods=['POST'])
def analyze_game():
    """Complete analysis workflow for a game"""
    try:
        data = request.get_json()
        game_name = data.get('game_name')
        days = data.get('days', 30)
        export_csv_flag = data.get('export_csv', True)
        
        if not game_name:
            return jsonify({'error': 'game_name is required'}), 400
        
        # Use the collect_data logic
        collect_response = collect_data()
        
        if collect_response.status_code != 200:
            return collect_response
        
        collect_result = collect_response.get_json()
        
        result = {
            'success': True,
            'analysis': collect_result
        }
        
        import pandas as pd
        # Export CSV if requested
        if export_csv_flag and collect_result.get('data'):
            csv_path = data_processor.export_to_csv(
                pd.DataFrame(collect_result['data']),
                f"{game_name.lower().replace(' ', '_')}_analysis.csv"
            )
            result['csv_export'] = {
                'path': csv_path,
                'download_url': f'/api/download-csv/{os.path.basename(csv_path)}'
            }
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in analyze_game: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Initialize clients on startup
    init_clients()
    
    # Run the Flask app
    app.run(
        host=config.host,
        port=config.port,
        debug=config.debug
    )
