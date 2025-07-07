# Steam Game Tracker

A comprehensive tracking system that monitors Steam game follower dynamics and correlates them with Reddit mentions to provide insights into social media buzz and engagement patterns.

## 🚀 Features

- **Steam Follower Tracking**: Scrape follower count data from SteamDB
- **Reddit Mentions Analysis**: Collect and analyze game mentions across Reddit
- **Data Correlation**: Compare Steam followers with social media activity
- **Interactive Visualization**: Beautiful charts and graphs using React and Recharts
- **CSV Export**: Export analysis results for further processing
- **REST API**: Clean API endpoints for data collection and analysis

## 🏗️ Architecture

### Backend (Python)
- **Flask** - Web framework and API server
- **PRAW** - Reddit API wrapper for collecting mentions
- **BeautifulSoup** - Web scraping for SteamDB data
- **Pandas** - Data processing and analysis
- **Requests** - HTTP client for web scraping

### Frontend (React + TypeScript)
- **React 19** - Modern UI framework
- **TypeScript** - Type-safe development
- **Recharts** - Data visualization
- **Axios** - HTTP client
- **Vite** - Fast development server

## 📋 Prerequisites

### For Reddit API Access
1. **Reddit Account** - You need a Reddit account
2. **Reddit App Registration** - Create an app at https://www.reddit.com/prefs/apps
   - Choose "script" type
   - Note down your `client_id` and `client_secret`

### Software Requirements
- **Python 3.8+**
- **Node.js 16+**
- **npm or yarn**

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd track_mentions_assessment
```

### 2. Backend Setup

#### Create Virtual Environment
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Environment Configuration
Create a `.env` file in the `backend` directory:

```env
# Reddit API Credentials (Required)
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=SteamMentionsTracker/1.0

# Optional Configuration
DATA_DIR=data
DAYS_TO_COLLECT=30
HOST=localhost
PORT=5000
DEBUG=true
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

## 🚀 Running the Application

### Start Backend Server
```bash
cd backend
python app.py
```
The API will be available at `http://localhost:5000`

### Start Frontend Development Server
```bash
cd frontend
npm run dev
```
The web interface will be available at `http://localhost:5173`

## 📖 Usage Guide

### Web Interface
1. **Enter Game Name**: Type the name of any Steam game (e.g., "Cyberpunk 2077")
2. **Select Time Period**: Choose how many days to analyze (7, 14, 30, or 60 days)
3. **Click Analyze**: The system will:
   - Search for the game on SteamDB
   - Collect current follower data
   - Search Reddit for mentions
   - Generate correlation analysis
4. **View Results**: See charts, statistics, and data tables
5. **Export Data**: Download results as CSV

### API Endpoints

#### Health Check
```http
GET /
```
Returns server status and service availability.

#### Search Game
```http
POST /api/search-game
Content-Type: application/json

{
  "game_name": "Cyberpunk 2077"
}
```

#### Collect Data
```http
POST /api/collect-data
Content-Type: application/json

{
  "game_name": "Cyberpunk 2077",
  "days": 30
}
```

#### Export CSV
```http
POST /api/export-csv
Content-Type: application/json

{
  "data": [...],
  "filename": "optional_custom_name.csv"
}
```

## 🔧 Configuration Options

### Game Parameters
- **Game Name**: Any Steam game title
- **Analysis Period**: 7-60 days (longer periods may take more time)
- **App ID**: Optional Steam App ID (will auto-detect if not provided)

### Reddit Search Settings
The system searches these subreddits by default:
- r/all (entire Reddit)
- r/gaming
- r/Steam
- r/pcgaming
- r/GameDeals
- r/tipofmyjoystick

### Data Sources
- **Steam Data**: SteamDB follower counts
- **Reddit Data**: Posts, comments, scores, and engagement metrics

## 📊 Output Format

### CSV Export
The exported CSV contains:
```csv
date,steam_followers_count,mentions_in_social_media
2024-01-15,25000,15
2024-01-16,25150,8
...
```

### Statistics Provided
- **Steam Followers**: Min, max, average, change over period
- **Reddit Mentions**: Total count, active days, engagement metrics
- **Correlation**: Statistical correlation between followers and mentions

## ⚠️ Important Notes

### Rate Limiting
- **SteamDB**: 1-2 requests per second (built-in delays)
- **Reddit API**: PRAW handles rate limiting automatically

### Data Accuracy
- **Steam Data**: Current implementation uses live data + simulated historical data
- **Reddit Data**: Real-time search results from Reddit API
- **Historical Data**: For production use, implement daily data collection

### Limitations
- SteamDB doesn't provide public historical follower APIs
- Reddit search is limited to recent posts (typically 1000 results per query)
- Some games may not be found if names don't match exactly

## 🔍 Troubleshooting

### Common Issues

#### "Reddit credentials not found"
- Ensure `.env` file exists in backend directory
- Verify `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` are set
- Check Reddit app configuration

#### "Game not found on SteamDB"
- Try different game name variations
- Check spelling and use exact Steam store names
- Some games may not be indexed on SteamDB

#### "No data available"
- Game might have no recent Reddit mentions
- Try a more popular game for testing
- Increase the analysis period

#### Frontend won't load
- Ensure backend is running on port 5000
- Check that both servers are running
- Verify proxy configuration in vite.config.ts

## 📈 Example Analysis

For a game like "Cyberpunk 2077":
- **Steam Followers**: ~500K followers
- **Reddit Mentions**: 50-200 mentions per day
- **Correlation**: Positive correlation during game updates/patches
- **Peak Activity**: Release dates, updates, controversy periods

## 🛡️ Security Considerations

- API credentials stored in environment variables
- No sensitive data exposed in frontend
- Rate limiting implemented for web scraping
- CORS configured for development

## 🔮 Future Enhancements

- **Real Historical Data**: Implement daily data collection service
- **More Platforms**: Twitter, YouTube, Twitch integration
- **Advanced Analytics**: Sentiment analysis, trend prediction
- **User Accounts**: Save favorite games and track over time
- **Alerts**: Notifications for significant changes
- **Database**: Persistent storage for historical data

## 📝 Development Notes

- Built for assessment purposes (2-3 hours development time)
- Focus on clean, readable code over production-scale features
- Demonstrates API integration, data processing, and visualization skills
- Extensible architecture for additional features

## 📄 License

This project is created as a technical assessment and is available for review and educational purposes.
