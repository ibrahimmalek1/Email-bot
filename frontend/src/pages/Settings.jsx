import { useState, useEffect } from 'react';
import { checkAuthStatus, checkGeminiStatus, saveGeminiKey, saveGoogleAuth, deleteAllSummaries } from '../api/api';
import './Settings.css';

function Settings() {
    const [authStatus, setAuthStatus] = useState(null);
    const [geminiStatus, setGeminiStatus] = useState(null);
    const [geminiKey, setGeminiKey] = useState('');
    const [clientId, setClientId] = useState('');
    const [clientSecret, setClientSecret] = useState('');
    const [saving, setSaving] = useState('');
    const [message, setMessage] = useState(null);

    useEffect(() => {
        loadStatus();
    }, []);

    const loadStatus = async () => {
        try {
            const [auth, gemini] = await Promise.all([
                checkAuthStatus(),
                checkGeminiStatus()
            ]);
            setAuthStatus(auth);
            setGeminiStatus(gemini);
        } catch (err) {
            console.error(err);
        }
    };

    const handleSaveGemini = async () => {
        if (!geminiKey.trim()) return;
        setSaving('gemini');
        try {
            const res = await saveGeminiKey(geminiKey);
            setMessage({ type: 'success', text: res.message });
            setGeminiKey('');
            loadStatus();
        } catch (err) {
            setMessage({ type: 'error', text: 'Failed to save' });
        } finally {
            setSaving('');
        }
    };

    const handleSaveGoogle = async () => {
        if (!clientId.trim() || !clientSecret.trim()) return;
        setSaving('google');
        try {
            const res = await saveGoogleAuth(clientId, clientSecret);
            setMessage({ type: 'success', text: res.message });
            loadStatus();
        } catch (err) {
            setMessage({ type: 'error', text: 'Failed to save' });
        } finally {
            setSaving('');
        }
    };

    const handleClearData = async () => {
        if (!confirm('Delete all email summaries? This cannot be undone.')) return;
        try {
            console.log('Attempting to delete all summaries...');
            const res = await deleteAllSummaries();
            console.log('Delete response:', res);
            setMessage({ type: 'success', text: 'All data cleared' });
        } catch (err) {
            console.error('Delete failed:', err);
            setMessage({ type: 'error', text: 'Failed to clear: ' + err.message });
        }
    };

    return (
        <div className="settings">
            <h1>⚙️ Settings</h1>

            {message && (
                <div className={`message ${message.type}`}>
                    {message.text}
                    <button onClick={() => setMessage(null)}>×</button>
                </div>
            )}

            {/* Gemini AI Section */}
            <div className="settings-section">
                <div className="section-header">
                    <h2>🤖 Gemini AI</h2>
                    <span className={`status-badge ${geminiStatus?.configured ? 'active' : ''}`}>
                        {geminiStatus?.configured ? '✅ Configured' : '⚠️ Not set'}
                    </span>
                </div>
                <p className="section-desc">
                    Enable AI-powered email summarization and smart categorization.
                    <a href="https://aistudio.google.com/apikey" target="_blank" rel="noreferrer">
                        Get free API key →
                    </a>
                </p>
                <div className="input-group">
                    <input
                        type="password"
                        placeholder="Enter Gemini API key"
                        value={geminiKey}
                        onChange={(e) => setGeminiKey(e.target.value)}
                    />
                    <button onClick={handleSaveGemini} disabled={saving === 'gemini' || !geminiKey.trim()}>
                        {saving === 'gemini' ? 'Saving...' : 'Save'}
                    </button>
                </div>
            </div>

            {/* Google OAuth Section */}
            <div className="settings-section">
                <div className="section-header">
                    <h2>🔐 Google OAuth</h2>
                    <span className={`status-badge ${authStatus?.authenticated ? 'active' : ''}`}>
                        {authStatus?.authenticated ? `✅ ${authStatus?.user?.email}` : '⚠️ Not connected'}
                    </span>
                </div>
                <p className="section-desc">
                    Connect your Gmail account to fetch emails.
                </p>

                {authStatus?.authenticated ? (
                    <a href="http://localhost:8000/auth/login" className="login-btn connected">
                        🔄 Reconnect Google Account
                    </a>
                ) : authStatus?.credentials_configured ? (
                    <a href="http://localhost:8000/auth/login" className="login-btn">
                        Sign in with Google
                    </a>
                ) : (
                    <>
                        <div className="input-group">
                            <input
                                type="text"
                                placeholder="Client ID"
                                value={clientId}
                                onChange={(e) => setClientId(e.target.value)}
                            />
                        </div>
                        <div className="input-group">
                            <input
                                type="password"
                                placeholder="Client Secret"
                                value={clientSecret}
                                onChange={(e) => setClientSecret(e.target.value)}
                            />
                            <button onClick={handleSaveGoogle} disabled={saving === 'google'}>
                                {saving === 'google' ? 'Saving...' : 'Save'}
                            </button>
                        </div>
                    </>
                )}
            </div>

            {/* Danger Zone */}
            <div className="settings-section danger">
                <h2>🗑️ Danger Zone</h2>
                <p className="section-desc">
                    Irreversible actions. Be careful!
                </p>
                <button className="danger-btn" onClick={handleClearData}>
                    Delete All Email Data
                </button>
            </div>
        </div>
    );
}

export default Settings;
