import { useState } from 'react';
import axios from 'axios';
import { Search, Download, TrendingUp, MessageCircle, Calendar, BarChart3 } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './App.css';

interface GameData {
  date: string;
  steam_followers_count: number;
  mentions_in_social_media: number;
}

interface Stats {
  date_range: {
    start: string;
    end: string;
    total_days: number;
  };
  steam_followers: {
    min: number;
    max: number;
    mean: number;
    change: number;
  };
  reddit_mentions: {
    total: number;
    min: number;
    max: number;
    mean: number;
    active_days: number;
  };
  correlation: number | null;
}

interface AnalysisResult {
  success: boolean;
  game_name: string;
  app_id: string;
  data: GameData[];
  stats: Stats;
  collected: {
    steam_points: number;
    reddit_mentions: number;
  };
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

function App() {
  const [gameName, setGameName] = useState('');
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState('');

  const handleAnalyze = async () => {
    if (!gameName.trim()) {
      setError('Please enter a game name');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/collect-data`, {
        game_name: gameName.trim(),
        days: days
      });

      setResult(response.data);
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.error || 'Failed to analyze game data');
      } else {
        setError('Failed to analyze game data');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = async () => {
    if (!result?.data) return;

    try {
      const response = await axios.post(`${API_BASE_URL}/api/export-csv`, {
        data: result.data,
        filename: `${result.game_name.toLowerCase().replace(/\s+/g, '_')}_analysis.csv`
      });

      if (response.data.download_url) {
        const link = document.createElement('a');
        link.href = `${API_BASE_URL}${response.data.download_url}`;
        link.download = `${result.game_name}_analysis.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  const formatChartData = () => {
    if (!result?.data) return [];
    
    return result.data.map(item => ({
      date: new Date(item.date).toLocaleDateString(),
      followers: item.steam_followers_count,
      mentions: item.mentions_in_social_media,
      fullDate: item.date
    }));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            Steam Game Tracker
          </h1>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Track Steam follower dynamics and Reddit mentions for any game. 
            Analyze correlations between social media buzz and Steam engagement.
          </p>
        </div>

        {/* Input Form */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8 max-w-2xl mx-auto">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Game Name
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  value={gameName}
                  onChange={(e) => setGameName(e.target.value)}
                  placeholder="Enter game name (e.g., 'Cyberpunk 2077')"
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Analysis Period (Days)
              </label>
              <select
                value={days}
                onChange={(e) => setDays(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value={7}>Last 7 days</option>
                <option value={14}>Last 14 days</option>
                <option value={30}>Last 30 days</option>
                <option value={60}>Last 60 days</option>
              </select>
            </div>

            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-medium py-2 px-4 rounded-md transition duration-200 flex items-center justify-center space-x-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <BarChart3 className="h-4 w-4" />
                  <span>Analyze Game</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8 max-w-2xl mx-auto">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-8">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <TrendingUp className="h-8 w-8 text-blue-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Steam Followers</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {result.stats.steam_followers.max.toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <MessageCircle className="h-8 w-8 text-orange-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Reddit Mentions</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {result.stats.reddit_mentions.total.toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <Calendar className="h-8 w-8 text-green-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Active Days</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {result.stats.reddit_mentions.active_days}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <BarChart3 className="h-8 w-8 text-purple-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Correlation</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {result.stats.correlation 
                        ? (result.stats.correlation * 100).toFixed(1) + '%'
                        : 'N/A'
                      }
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Charts */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-800">
                  {result.game_name} - Followers vs Mentions
                </h2>
                <button
                  onClick={handleExportCSV}
                  className="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-md transition duration-200 flex items-center space-x-2"
                >
                  <Download className="h-4 w-4" />
                  <span>Export CSV</span>
                </button>
              </div>

              <div className="h-96 mb-8">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={formatChartData()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="date" 
                      tick={{ fontSize: 12 }}
                      angle={-45}
                      textAnchor="end"
                      height={60}
                    />
                    <YAxis yAxisId="followers" orientation="left" />
                    <YAxis yAxisId="mentions" orientation="right" />
                    <Tooltip 
                      labelFormatter={(label: string) => `Date: ${label}`}
                      formatter={(value: number, name: string) => [
                        name === 'followers' ? value.toLocaleString() : value,
                        name === 'followers' ? 'Steam Followers' : 'Reddit Mentions'
                      ]}
                    />
                    <Legend />
                    <Line
                      yAxisId="followers"
                      type="monotone"
                      dataKey="followers"
                      stroke="#2563eb"
                      strokeWidth={2}
                      dot={{ r: 4 }}
                      name="Steam Followers"
                    />
                    <Line
                      yAxisId="mentions"
                      type="monotone"
                      dataKey="mentions"
                      stroke="#ea580c"
                      strokeWidth={2}
                      dot={{ r: 4 }}
                      name="Reddit Mentions"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Data Table */}
              <div className="overflow-x-auto">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Data Table</h3>
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Date
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Steam Followers Count
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Mentions in Social Media
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {result.data.slice(0, 10).map((row, index) => (
                      <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {new Date(row.date).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {row.steam_followers_count.toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {row.mentions_in_social_media}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {result.data.length > 10 && (
                  <p className="text-sm text-gray-500 mt-2">
                    Showing first 10 rows of {result.data.length} total entries.
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
