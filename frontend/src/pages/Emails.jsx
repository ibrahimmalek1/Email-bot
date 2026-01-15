import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { getEmailSummaries, fetchEmails } from '../api/api';
import EmailCard from '../components/EmailCard';
import FilterBar from '../components/FilterBar';
import SummaryWidget from '../components/SummaryWidget';
import './Emails.css';

function Emails() {
    const [searchParams, setSearchParams] = useSearchParams();
    const [emails, setEmails] = useState([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [filters, setFilters] = useState({
        category: searchParams.get('category') || '',
        priority: searchParams.get('priority') || '',
        sender_type: searchParams.get('sender_type') || '',
        date_range: searchParams.get('date_range') || '',
        action_required: searchParams.get('action_required') === 'true' ? true : null,
        limit: ''
    });

    useEffect(() => {
        loadEmails();
    }, [filters, search]);

    const loadEmails = async () => {
        setLoading(true);
        try {
            const queryFilters = { ...filters };
            if (search) queryFilters.search = search;

            // Remove empty values
            Object.keys(queryFilters).forEach(key => {
                if (queryFilters[key] === '' || queryFilters[key] === null) {
                    delete queryFilters[key];
                }
            });

            const data = await getEmailSummaries(queryFilters);
            setEmails(data.data || []);
            setTotal(data.total || 0);
        } catch (err) {
            console.error('Error loading emails:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleFilterChange = (key, value) => {
        setFilters(prev => ({ ...prev, [key]: value }));

        // Update URL params
        setSearchParams(prev => {
            if (value) {
                prev.set(key, value);
            } else {
                prev.delete(key);
            }
            return prev;
        });
    };

    const handleClearFilters = () => {
        setFilters({
            category: '',
            priority: '',
            sender_type: '',
            date_range: '',
            action_required: null,
            limit: ''
        });
        setSearch('');
        setSearchParams({});
    };

    const handleSync = async () => {
        setLoading(true);
        try {
            // Fetch 10 most recent emails
            await fetchEmails({ limit: 10, days_back: 7 });
            await loadEmails(); // Reload from storage
        } catch (err) {
            console.error('Sync failed:', err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="emails-page">
            <div className="emails-main">
                <div className="emails-header">
                    <div className="emails-title">
                        <h1>📬 Inbox</h1>
                        <span className="email-count">
                            {loading ? '...' : `${emails.length} of ${total}`}
                        </span>
                        <button className="sync-btn" onClick={handleSync} disabled={loading} title="Fetch new emails">
                            🔄 Sync
                        </button>
                    </div>
                    <div className="search-box">
                        <input
                            type="text"
                            placeholder="🔍 Search emails..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>
                </div>

                <FilterBar
                    filters={filters}
                    onFilterChange={handleFilterChange}
                    onClear={handleClearFilters}
                />

                <SummaryWidget filters={filters} />


                <div className="emails-content">
                    {loading ? (
                        <div className="emails-loading">Loading emails...</div>
                    ) : emails.length === 0 ? (
                        <div className="emails-empty">
                            <span className="empty-icon">📭</span>
                            <p>No emails found</p>
                            <span className="empty-hint">Try adjusting your filters or fetch new emails</span>
                        </div>
                    ) : (
                        <div className="emails-grid">
                            {emails.map(email => (
                                <EmailCard key={email.id} email={email} />
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default Emails;
