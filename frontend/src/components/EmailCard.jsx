import './EmailCard.css';

function EmailCard({ email }) {
    const priorityColors = {
        high: '#ef4444',
        medium: '#f59e0b',
        low: '#22c55e'
    };

    const categoryIcons = {
        primary: '📧',
        social: '👥',
        promotions: '🏷️',
        updates: '🔔',
        forums: '💬'
    };

    const formatDate = (dateStr) => {
        const date = new Date(dateStr);
        const now = new Date();
        const diff = now - date;

        if (diff < 86400000) {
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } else if (diff < 604800000) {
            return date.toLocaleDateString([], { weekday: 'short' });
        }
        return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    };

    return (
        <div className="email-card">
            <div className="email-header">
                <span className="email-category">
                    {categoryIcons[email.category] || '📧'}
                </span>
                <span
                    className="email-priority"
                    style={{ background: priorityColors[email.priority] || '#6b7280' }}
                >
                    {email.priority}
                </span>
                {email.action_required && (
                    <span className="email-action-badge">⚡ Action</span>
                )}
            </div>

            <h3 className="email-subject">{email.subject || 'No Subject'}</h3>

            <div className="email-meta">
                <span className="email-sender">{email.sender}</span>
                <span className="email-date">{formatDate(email.date)}</span>
            </div>

            {/* Always show full summary */}
            <p className="email-summary">{email.summary}</p>

            <div className="email-footer">
                <span className="email-sender-type">{email.sender_type}</span>
                {email.has_attachments && <span className="email-attachment">📎</span>}
            </div>
        </div>
    );
}

export default EmailCard;
