import React from 'react';
import { Search, Filter, X } from 'lucide-react';

interface ScheduleFiltersProps {
    filters: {
        teacher: string;
        weekday: string;
        name: string;
        is_active: string;
    };
    onFilterChange: (key: string, value: string) => void;
    onClearFilters: () => void;
    teachers: string[];
}

export const ScheduleFilters: React.FC<ScheduleFiltersProps> = ({
    filters,
    onFilterChange,
    onClearFilters,
    teachers,
}) => {
    const weekdays = [
        { value: '', label: 'All days' },
        { value: '1', label: 'Monday' },
        { value: '2', label: 'Tuesday' },
        { value: '3', label: 'Wednesday' },
        { value: '4', label: 'Thursday' },
        { value: '5', label: 'Friday' },
        { value: '6', label: 'Saturday' },
        { value: '7', label: 'Sunday' },
    ];

    const activeOptions = [
        { value: '', label: 'All classes' },
        { value: 'true', label: 'Available classes' },
        { value: 'false', label: 'Unavailable classes' },
    ];

    const hasActiveFilters =
        filters.teacher !== '' ||
        filters.weekday !== '' ||
        filters.name !== '' ||
        filters.is_active === 'false' ||
        filters.is_active === '';

    // Debug logs
    console.log('ScheduleFilters render:', {
        filters,
        hasActiveFilters,
        teachersCount: teachers.length
    });

    const handleFilterChange = (key: string, value: string) => {
        console.log('Filter change:', { key, value, oldValue: filters[key as keyof typeof filters] });
        onFilterChange(key, value);
    };

    return (
        <div className="card mb-6">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                    <Filter className="h-5 w-5 text-gray-600" />
                    <h3 className="text-lg font-semibold text-gray-900">Filters</h3>
                </div>

                {hasActiveFilters && (
                    <button
                        onClick={onClearFilters}
                        className="flex items-center space-x-1 text-sm text-gray-600 hover:text-gray-800"
                    >
                        <X className="h-4 w-4" />
                        <span>Clear</span>
                    </button>
                )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Search by name */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Search by name
                    </label>
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                        <input
                            type="text"
                            value={filters.name}
                            onChange={(e) => handleFilterChange('name', e.target.value)}
                            placeholder="Class name..."
                            className="input-field pl-10"
                        />
                    </div>
                </div>

                {/* Teacher filter */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Teacher
                    </label>
                    <select
                        value={filters.teacher}
                        onChange={(e) => handleFilterChange('teacher', e.target.value)}
                        className="input-field"
                    >
                        <option value="">All teachers</option>
                        {teachers.map((teacher) => (
                            <option key={teacher} value={teacher}>
                                {teacher}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Weekday filter */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Day of week
                    </label>
                    <select
                        value={filters.weekday}
                        onChange={(e) => handleFilterChange('weekday', e.target.value)}
                        className="input-field"
                    >
                        {weekdays.map((weekday) => (
                            <option key={weekday.value} value={weekday.value}>
                                {weekday.label}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Status filter */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Class availability
                    </label>
                    <select
                        value={filters.is_active}
                        onChange={(e) => handleFilterChange('is_active', e.target.value)}
                        className="input-field"
                    >
                        {activeOptions.map((option) => (
                            <option key={option.value} value={option.value}>
                                {option.label}
                            </option>
                        ))}
                    </select>
                </div>
            </div>
        </div>
    );
}; 