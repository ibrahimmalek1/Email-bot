import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navbar.css';

function Navbar() {
    const location = useLocation();
    const [menuOpen, setMenuOpen] = useState(false);

    const isActive = (path) => location.pathname === path;

    return (
        <nav className="navbar">
            <div className="navbar-brand">
                <span className="navbar-logo">📧</span>
                <span className="navbar-title">Email Summarizer</span>
            </div>

            <button className="navbar-toggle" onClick={() => setMenuOpen(!menuOpen)}>
                ☰
            </button>

            <div className={`navbar-links ${menuOpen ? 'open' : ''}`}>
                <Link to="/" className={`navbar-link ${isActive('/') ? 'active' : ''}`}>
                    📊 Dashboard
                </Link>
                <Link to="/emails" className={`navbar-link ${isActive('/emails') ? 'active' : ''}`}>
                    📬 Emails
                </Link>
                <Link to="/settings" className={`navbar-link ${isActive('/settings') ? 'active' : ''}`}>
                    ⚙️ Settings
                </Link>
            </div>
        </nav>
    );
}

export default Navbar;
