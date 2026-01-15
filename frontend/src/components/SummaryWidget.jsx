import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { generateSummaryReport } from '../api/api';
import './SummaryWidget.css';

const SummaryWidget = ({ filters }) => {
    const [report, setReport] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [expanded, setExpanded] = useState(true);

    const handleGenerate = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await generateSummaryReport(filters);
            setReport(data.report);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    // Auto-generate only on first load or manual trigger to save quota? 
    // Let's stick to manual or "fresh" button for now, or auto-generate if explicitly requested.
    // User asked "should appear at the top... like user apply any filter ... report should come according to that"
    // Ideally it auto-updates.

    useEffect(() => {
        // Debounce to prevent rapid calls
        const timer = setTimeout(() => {
            if (filters) {
                handleGenerate();
            }
        }, 1000);
        return () => clearTimeout(timer);
    }, [filters]);

    if (!expanded) {
        return (
            <div className="summary-widget-collapsed" onClick={() => setExpanded(true)}>
                <span>✨ Show Executive Summary</span>
            </div>
        );
    }

    return (
        <div className="summary-widget">
            <div className="summary-header">
                <div className="summary-title">
                    <h3>✨ Executive Summary</h3>
                    <span className="ai-badge">AI Generated</span>
                </div>
                <div className="summary-actions">
                    <button className="refresh-btn" onClick={handleGenerate} disabled={loading} title="Regenerate">
                        {loading ? '🔄' : '↻'}
                    </button>
                    <button className="collapse-btn" onClick={() => setExpanded(false)} title="Collapse">
                        &minus;
                    </button>
                </div>
            </div>

            <div className="summary-content">
                {loading ? (
                    <div className="summary-loading">
                        <div className="shimmer-line"></div>
                        <div className="shimmer-line"></div>
                        <div className="shimmer-line width-70"></div>
                    </div>
                ) : error ? (
                    <div className="summary-error">{error}</div>
                ) : (
                    <div className="markdown-body">
                        <ReactMarkdown>{report || "Select filters to generate a summary."}</ReactMarkdown>
                    </div>
                )}
            </div>
        </div>
    );
};

export default SummaryWidget;
