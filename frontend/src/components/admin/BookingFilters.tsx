import React, { useState } from 'react';
import { Search, Calendar, User, Users, Filter } from 'lucide-react';

interface BookingFiltersProps {
    onFiltersChange: (filters: BookingFilters) => void;
    users: any[];
    teachers: string[];
    classNames: string[];
}

export interface BookingFilters {
    startDate?: string;
    endDate?: string;
    userId?: string;
    teacher?: string;
    className?: string;
    timeRange?: string;
}

export const BookingFilters: React.FC<BookingFiltersProps> = ({
    onFiltersChange,
    users,
    teachers,
    classNames
}) => {
    const [isExpanded, setIsExpanded] = useState(true); // По умолчанию развернуто
    const [filters, setFilters] = useState<BookingFilters>(() => {
        // Устанавливаем фильтр по умолчанию на текущий месяц
        const now = new Date();
        const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
        const endOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0);

        const defaultFilters: BookingFilters = {
            startDate: startOfMonth.toISOString().split('T')[0],
            endDate: endOfMonth.toISOString().split('T')[0]
        };

        // Вызываем onFiltersChange с дефолтными фильтрами только один раз при монтировании
        setTimeout(() => onFiltersChange(defaultFilters), 0);

        return defaultFilters;
    });

    const handleFilterChange = (key: keyof BookingFilters, value: string | undefined) => {
        const newFilters = { ...filters, [key]: value };
        setFilters(newFilters);
        onFiltersChange(newFilters);
    };

    const clearFilters = () => {
        const emptyFilters: BookingFilters = {};
        setFilters(emptyFilters);
        onFiltersChange(emptyFilters);
    };

    const hasActiveFilters = Object.values(filters).some(value => value !== undefined && value !== '');

    return (
        <div className="card mb-6">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                    <Filter className="h-5 w-5 text-gray-500" />
                    <h3 className="text-lg font-medium text-gray-900">Filters</h3>
                </div>
                <div className="flex items-center space-x-2">
                    <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        className="text-sm text-gray-600 hover:text-gray-900"
                    >
                        {isExpanded ? 'Hide' : 'Show'} filters
                    </button>
                    {hasActiveFilters && (
                        <button
                            onClick={clearFilters}
                            className="text-sm text-red-600 hover:text-red-800"
                        >
                            Clear all
                        </button>
                    )}
                </div>
            </div>

            {isExpanded && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {/* Date Range */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            <Calendar className="h-4 w-4 inline mr-1" />
                            Start Date
                        </label>
                        <input
                            type="date"
                            value={filters.startDate || ''}
                            onChange={(e) => handleFilterChange('startDate', e.target.value || undefined)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            <Calendar className="h-4 w-4 inline mr-1" />
                            End Date
                        </label>
                        <input
                            type="date"
                            value={filters.endDate || ''}
                            onChange={(e) => handleFilterChange('endDate', e.target.value || undefined)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                    </div>

                    {/* Client Filter */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            <User className="h-4 w-4 inline mr-1" />
                            Client
                        </label>
                        <select
                            value={filters.userId || ''}
                            onChange={(e) => handleFilterChange('userId', e.target.value || undefined)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                        >
                            <option value="">All clients</option>
                            {users.map((user) => (
                                <option key={user.id} value={user.id}>
                                    {user.name} ({user.email})
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Teacher Filter */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            <Users className="h-4 w-4 inline mr-1" />
                            Teacher
                        </label>
                        <select
                            value={filters.teacher || ''}
                            onChange={(e) => handleFilterChange('teacher', e.target.value || undefined)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                        >
                            <option value="">All teachers</option>
                            {teachers.map((teacher) => (
                                <option key={teacher} value={teacher}>
                                    {teacher}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Class Name Filter */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            <Search className="h-4 w-4 inline mr-1" />
                            Class/Direction
                        </label>
                        <select
                            value={filters.className || ''}
                            onChange={(e) => handleFilterChange('className', e.target.value || undefined)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                        >
                            <option value="">All classes</option>
                            {classNames.map((className) => (
                                <option key={className} value={className}>
                                    {className}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Time Range Filter */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            <Calendar className="h-4 w-4 inline mr-1" />
                            Time Range
                        </label>
                        <select
                            value={filters.timeRange || ''}
                            onChange={(e) => handleFilterChange('timeRange', e.target.value || undefined)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                        >
                            <option value="">All times</option>
                            <option value="morning">Morning (6:00-12:00)</option>
                            <option value="afternoon">Afternoon (12:00-18:00)</option>
                            <option value="evening">Evening (18:00-24:00)</option>
                        </select>
                    </div>
                </div>
            )}
        </div>
    );
}; 