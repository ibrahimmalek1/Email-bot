import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import StatsCard from '../components/StatsCard';
import { getEmailStats, checkAuthStatus, checkGeminiStatus, fetchEmails } from '../api/api';
import './Dashboard.css';

function Dashboard() {
    const [stats, setStats] = useState(null);
    const [authStatus, setAuthStatus] = useState(null);
    const [geminiStatus, setGeminiStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [fetching, setFetching] = useState(false);
    const [nextPageToken, setNextPageToken] = useState(null);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [statsData, authData, geminiData] = await Promise.all([
                getEmailStats(),
                checkAuthStatus(),
                checkGeminiStatus()
            ]);
            setStats(statsData);
            setAuthStatus(authData);
            setGeminiStatus(geminiData);
        } catch (err) {
            console.error('Error loading data:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleFetchEmails = async () => {
        setFetching(true);
        try {
            // Use existing page token if available, otherwise start fresh
            const params = { limit: 50, days_back: 1000 };
            if (nextPageToken) {
                params.page_token = nextPageToken;
            }

            const res = await fetchEmails(params);

            if (res.success) {
                setNextPageToken(res.next_page_token || null);
            }

            await loadData();
        } catch (err) {
            console.error('Error fetching:', err);
        } finally {
            setFetching(false);
        }
    };

    if (loading) {
        return <div className="dashboard loading">Loading...</div>;
    }

    const isLoggedIn = authStatus?.authenticated;
    const isAiEnabled = geminiStatus?.configured;

    return (
        <div className="dashboard">
            <div className="dashboard-header">
                <h1>📊 Dashboard</h1>
                <div className="header-actions">
                    <button
                        className="fetch-button"
                        onClick={handleFetchEmails}
                        disabled={fetching || !isLoggedIn}
                    >
                        {fetching ? '⏳ Fetching...' : nextPageToken ? '📥 Fetch More Emails' : '🔄 Fetch New Emails'}
                    </button>
                    {nextPageToken && (
                        <button
                            className="reset-fetch-btn"
                            onClick={() => setNextPageToken(null)}
                            title="Reset to newest"
                        >
                            ⏮️
                        </button>
                    )}
                </div>
            </div>

            {/* Status Cards */}
            <div className="status-row">
                <div className={`status-card ${isLoggedIn ? 'success' : 'warning'}`}>
                    <span className="status-icon">{isLoggedIn ? '✅' : '⚠️'}</span>
                    <div className="status-info">
                        <span className="status-title">Google Login</span>
                        <span className="status-text">
                            {isLoggedIn ? authStatus?.user?.email : 'Not connected'}
                        </span>
                    </div>
                    {!isLoggedIn && (
                        <a href="http://localhost:8000/auth/login" className="status-action">
                            Login
                        </a>
                    )}
                </div>

                <div className={`status-card ${isAiEnabled ? 'success' : 'warning'}`}>
                    <span className="status-icon">{isAiEnabled ? '✅' : '⚠️'}</span>
                    <div className="status-info">
                        <span className="status-title">Gemini AI</span>
                        <span className="status-text">
                            {isAiEnabled ? 'Enabled' : 'Not configured'}
                        </span>
                    </div>
                    {!isAiEnabled && (
                        <Link to="/settings" className="status-action">Configure</Link>
                    )}
                </div>
            </div>

            {/* Stats Grid */}
            {stats && (
                <div className="stats-grid">
                    <StatsCard
                        title="Total Emails"
                        value={stats.total || 0}
                        icon="📧"
                        color="#6366f1"
                    />
                    <StatsCard
                        title="Action Required"
                        value={stats.action_required || 0}
                        icon="⚡"
                        color="#ef4444"
                    />
                    <StatsCard
                        title="High Priority"
                        value={stats.by_priority?.high || 0}
                        icon="🔴"
                        color="#f59e0b"
                    />
                    <StatsCard
                        title="With Attachments"
                        value={stats.with_attachments || 0}
                        icon="📎"
                        color="#22c55e"
                    />
                </div>
            )}

            {/* Category Breakdown */}
            {stats && stats.by_category && (
                <div className="breakdown-section">
                    <h2>📂 By Category</h2>
                    <div className="breakdown-grid">
                        {Object.entries(stats.by_category).map(([cat, count]) => (
                            <Link to={`/emails?category=${cat}`} key={cat} className="breakdown-item">
                                <span className="breakdown-label">{cat}</span>
                                <span className="breakdown-value">{count}</span>
                            </Link>
                        ))}
                    </div>
                </div>
            )}

            {/* Quick Actions */}
            <div className="quick-actions">
                <h2>🚀 Quick Actions</h2>
                <div className="action-buttons">
                    <Link to="/emails?priority=high" className="action-btn high">
                        🔴 High Priority
                    </Link>
                    <Link to="/emails?action_required=true" className="action-btn action">
                        ⚡ Needs Action
                    </Link>
                    <Link to="/emails?date_range=today" className="action-btn today">
                        📅 Today's Emails
                    </Link>
                    <Link to="/emails" className="action-btn all">
                        📬 All Emails
                    </Link>
                </div>
            </div>
        </div>
    );
}

export default Dashboard;
