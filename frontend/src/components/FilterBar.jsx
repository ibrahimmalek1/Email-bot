import { useState, useEffect, useRef } from 'react';
import './FilterBar.css';

function FilterBar({ filters, onFilterChange, onClear }) {
    const categories = ['primary', 'social', 'promotions', 'updates'];
    const priorities = ['high', 'medium', 'low'];
    const senderTypes = ['person', 'company', 'newsletter', 'automated'];
    const dateRanges = [
        { value: 'today', label: 'Today' },
        { value: 'week', label: 'This Week' },
        { value: 'month', label: 'This Month' }
    ];

    const [openDropdown, setOpenDropdown] = useState(null);
    const filterRef = useRef(null);

    // Close dropdowns when clicking outside
    useEffect(() => {
        function handleClickOutside(event) {
            if (filterRef.current && !filterRef.current.contains(event.target)) {
                setOpenDropdown(null);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, []);

    const toggleDropdown = (name) => {
        setOpenDropdown(openDropdown === name ? null : name);
    };

    return (
        <div className="filter-bar" ref={filterRef}>
            <div className="filter-groups">
                {/* Category Dropdown */}
                <div className="filter-dropdown-container">
                    <button
                        className={`filter-btn ${filters.category ? 'active' : ''}`}
                        onClick={() => toggleDropdown('category')}
                    >
                        Category {filters.category ? `: ${filters.category}` : '▾'}
                    </button>
                    {openDropdown === 'category' && (
                        <div className="filter-dropdown">
                            <button
                                className={!filters.category ? 'active' : ''}
                                onClick={() => { onFilterChange('category', ''); setOpenDropdown(null); }}
                            >
                                All
                            </button>
                            {categories.map(cat => (
                                <button
                                    key={cat}
                                    className={filters.category === cat ? 'active' : ''}
                                    onClick={() => { onFilterChange('category', cat); setOpenDropdown(null); }}
                                >
                                    {cat}
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {/* Priority Dropdown */}
                <div className="filter-dropdown-container">
                    <button
                        className={`filter-btn ${filters.priority ? 'active' : ''}`}
                        onClick={() => toggleDropdown('priority')}
                    >
                        Priority {filters.priority ? `: ${filters.priority}` : '▾'}
                    </button>
                    {openDropdown === 'priority' && (
                        <div className="filter-dropdown">
                            <button
                                className={!filters.priority ? 'active' : ''}
                                onClick={() => { onFilterChange('priority', ''); setOpenDropdown(null); }}
                            >
                                All
                            </button>
                            {priorities.map(pri => (
                                <button
                                    key={pri}
                                    className={`priority-${pri} ${filters.priority === pri ? 'active' : ''}`}
                                    onClick={() => { onFilterChange('priority', pri); setOpenDropdown(null); }}
                                >
                                    {pri}
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {/* Sender Type Dropdown */}
                <div className="filter-dropdown-container">
                    <button
                        className={`filter-btn ${filters.sender_type ? 'active' : ''}`}
                        onClick={() => toggleDropdown('sender_type')}
                    >
                        Sender {filters.sender_type ? `: ${filters.sender_type}` : '▾'}
                    </button>
                    {openDropdown === 'sender_type' && (
                        <div className="filter-dropdown">
                            <button
                                className={!filters.sender_type ? 'active' : ''}
                                onClick={() => { onFilterChange('sender_type', ''); setOpenDropdown(null); }}
                            >
                                All
                            </button>
                            {senderTypes.map(type => (
                                <button
                                    key={type}
                                    className={filters.sender_type === type ? 'active' : ''}
                                    onClick={() => { onFilterChange('sender_type', type); setOpenDropdown(null); }}
                                >
                                    {type}
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {/* Date Range Dropdown */}
                <div className="filter-dropdown-container">
                    <button
                        className={`filter-btn ${filters.date_range ? 'active' : ''}`}
                        onClick={() => toggleDropdown('date_range')}
                    >
                        Time {filters.date_range ? `: ${filters.date_range}` : '▾'}
                    </button>
                    {openDropdown === 'date_range' && (
                        <div className="filter-dropdown">
                            <button
                                className={!filters.date_range ? 'active' : ''}
                                onClick={() => { onFilterChange('date_range', ''); setOpenDropdown(null); }}
                            >
                                Anytime
                            </button>
                            {dateRanges.map(dr => (
                                <button
                                    key={dr.value}
                                    className={filters.date_range === dr.value ? 'active' : ''}
                                    onClick={() => { onFilterChange('date_range', dr.value); setOpenDropdown(null); }}
                                >
                                    {dr.label}
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {/* Action Required Toggle */}
                <button
                    className={`filter-toggle ${filters.action_required ? 'active' : ''}`}
                    onClick={() => onFilterChange('action_required', filters.action_required ? null : true)}
                >
                    Action Required
                </button>
            </div>

            <div className="filter-actions">
                <button className="filter-reset" onClick={onClear}>Reset</button>
            </div>
        </div>
    );
}

export default FilterBar;
