import './StatsCard.css';

function StatsCard({ title, value, icon, color, subtitle }) {
    return (
        <div className="stats-card" style={{ borderColor: color }}>
            <div className="stats-icon" style={{ background: color }}>
                {icon}
            </div>
            <div className="stats-content">
                <div className="stats-value">{value}</div>
                <div className="stats-title">{title}</div>
                {subtitle && <div className="stats-subtitle">{subtitle}</div>}
            </div>
        </div>
    );
}

export default StatsCard;
