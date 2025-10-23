import React from 'react';
import { DanceClass } from '@/types';
import { WEEKDAYS } from '@/types';
import { Clock, Users, User, Calendar } from 'lucide-react';

interface ScheduleCardProps {
    danceClass: DanceClass;
    onBook?: (danceClass: DanceClass) => void;
    isBooked?: boolean;
    isAdmin?: boolean;
    onEdit?: (danceClass: DanceClass) => void;
    onDelete?: (id: string) => void;
}

export const ScheduleCard: React.FC<ScheduleCardProps> = ({
    danceClass,
    onBook,
    isBooked = false,
    isAdmin = false,
    onEdit,
    onDelete,
}) => {
    const formatTime = (time: string) => {
        return time ? time.substring(0, 5) : 'N/A'; // Remove seconds
    };

    const getWeekdayName = (weekday: number) => {
        return WEEKDAYS[weekday as keyof typeof WEEKDAYS] || 'Unknown';
    };

    return (
        <div className="card-hover group">
            <div className="flex items-start justify-between mb-4">
                <div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-1">
                        {danceClass.name}
                    </h3>
                    <div className="flex items-center text-gray-600 mb-2">
                        <User className="h-4 w-4 mr-1" />
                        <span className="text-sm">{danceClass.teacher}</span>
                    </div>
                </div>

                <div className="flex items-center space-x-2">
                    {danceClass.active ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            Active
                        </span>
                    ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            Inactive
                        </span>
                    )}
                </div>
            </div>

            <div className="space-y-3 mb-4">
                <div className="flex items-center text-gray-600">
                    <Calendar className="h-4 w-4 mr-2" />
                    <span className="text-sm">{getWeekdayName(danceClass.weekday)}</span>
                </div>

                <div className="flex items-center text-gray-600">
                    <Clock className="h-4 w-4 mr-2" />
                    <span className="text-sm">{formatTime(danceClass.start_time)}</span>
                </div>

                <div className="flex items-center text-gray-600">
                    <Users className="h-4 w-4 mr-2" />
                    <span className="text-sm">Capacity: {danceClass.capacity} people</span>
                </div>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                {isAdmin ? (
                    <div className="flex space-x-2">
                        <button
                            onClick={() => onEdit?.(danceClass)}
                            className="btn-secondary text-sm px-3 py-1"
                        >
                            Edit
                        </button>
                        <button
                            onClick={() => onDelete?.(danceClass.id)}
                            className="btn-danger text-sm px-3 py-1"
                        >
                            Delete
                        </button>
                    </div>
                ) : (
                    <button
                        onClick={() => onBook?.(danceClass)}
                        disabled={!danceClass.active}
                        className={`w-full text-sm px-4 py-2 rounded-lg font-medium transition-colors duration-200 ${danceClass.active
                            ? 'btn-primary'
                            : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            }`}
                    >
                        {danceClass.active ? 'Book' : 'Class inactive'}
                    </button>
                )}
            </div>
        </div>
    );
}; 