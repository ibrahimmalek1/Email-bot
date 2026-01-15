import { NavLink, useNavigate } from 'react-router-dom';
import { getLoginUrl } from '../api/api';
import './Sidebar.css';

function Sidebar() {
    const navigate = useNavigate();

    const handleLogout = () => {
        // For Google OAuth, a full logout might require clearing cookies/tokens
        // But for this app, we can just redirect to login or clear local state if any
        window.location.href = getLoginUrl();
    };

    return (
        <aside className="sidebar">
            <div className="sidebar-header">
                <div className="logo-container">
                    <span className="logo-icon">🤖</span>
                    <span className="logo-text">Summarizer</span>
                </div>
            </div>

            <nav className="sidebar-nav">
                <NavLink
                    to="/"
                    className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                >
                    <span className="nav-icon">📊</span>
                    <span className="nav-label">Dashboard</span>
                </NavLink>

                <NavLink
                    to="/emails"
                    className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                >
                    <span className="nav-icon">📬</span>
                    <span className="nav-label">Emails</span>
                </NavLink>

                <NavLink
                    to="/settings"
                    className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                >
                    <span className="nav-icon">⚙️</span>
                    <span className="nav-label">Settings</span>
                </NavLink>


            </nav>

            <div className="sidebar-footer">
                <button className="logout-button" onClick={handleLogout}>
                    <span className="nav-icon">🚪</span>
                    <span className="nav-label">Logout</span>
                </button>
            </div>
        </aside>
    );
}

export default Sidebar;
