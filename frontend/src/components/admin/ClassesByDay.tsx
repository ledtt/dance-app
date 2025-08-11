import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Calendar, Clock, Users, Edit, Trash2 } from 'lucide-react';

interface ClassData {
    id: string;
    name: string;
    teacher: string;
    weekday: number;
    start_time: string;
    capacity: number;
    comment?: string;
    active: boolean;
}

interface ClassesByDayProps {
    classes: ClassData[];
    onEditClass: (danceClass: ClassData) => void;
    onDeleteClass: (id: string) => void;
}

const weekdayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const weekdayShortNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

export const ClassesByDay: React.FC<ClassesByDayProps> = ({ classes, onEditClass, onDeleteClass }) => {
    const [expandedDays, setExpandedDays] = useState<Set<number>>(new Set());

    const toggleDay = (weekday: number) => {
        const newExpanded = new Set(expandedDays);
        if (newExpanded.has(weekday)) {
            newExpanded.delete(weekday);
        } else {
            newExpanded.add(weekday);
        }
        setExpandedDays(newExpanded);
    };

    // Group classes by weekday
    const classesByWeekday = classes.reduce((acc, danceClass) => {
        const weekday = danceClass.weekday;
        if (!acc[weekday]) {
            acc[weekday] = [];
        }
        acc[weekday].push(danceClass);
        return acc;
    }, {} as Record<number, ClassData[]>);

    // Sort classes within each day by start time
    Object.keys(classesByWeekday).forEach(weekday => {
        classesByWeekday[parseInt(weekday)].sort((a, b) => {
            return a.start_time.localeCompare(b.start_time);
        });
    });

    return (
        <div className="space-y-4">
            {weekdayNames.map((dayName, index) => {
                const weekday = index + 1;
                const dayClasses = classesByWeekday[weekday] || [];
                const isExpanded = expandedDays.has(weekday);

                if (dayClasses.length === 0) {
                    return null;
                }

                return (
                    <div key={weekday} className="border border-gray-200 rounded-lg">
                        <button
                            onClick={() => toggleDay(weekday)}
                            className="w-full px-4 py-3 flex items-center justify-between bg-gray-50 hover:bg-gray-100 transition-colors rounded-t-lg"
                        >
                            <div className="flex items-center space-x-3">
                                {isExpanded ? (
                                    <ChevronDown className="h-4 w-4 text-gray-500" />
                                ) : (
                                    <ChevronRight className="h-4 w-4 text-gray-500" />
                                )}
                                <span className="font-medium text-gray-900">{dayName}</span>
                                <span className="text-sm text-gray-500">({dayClasses.length} classes)</span>
                            </div>
                        </button>

                        {isExpanded && (
                            <div className="p-4 space-y-3">
                                {dayClasses.map((danceClass) => (
                                    <div key={danceClass.id} className="card">
                                        <div className="flex items-start justify-between mb-3">
                                            <div>
                                                <h3 className="text-lg font-semibold text-gray-900">
                                                    {danceClass.name}
                                                </h3>
                                                <p className="text-sm text-gray-600">{danceClass.teacher}</p>
                                            </div>
                                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${danceClass.active
                                                ? 'bg-green-100 text-green-800'
                                                : 'bg-gray-100 text-gray-800'
                                                }`}>
                                                {danceClass.active ? 'Active' : 'Inactive'}
                                            </span>
                                        </div>

                                        <div className="space-y-2 mb-3">
                                            <div className="flex items-center text-gray-600">
                                                <Clock className="h-4 w-4 mr-2" />
                                                <span className="text-sm">{danceClass.start_time ? danceClass.start_time.substring(0, 5) : 'N/A'}</span>
                                            </div>
                                            <div className="flex items-center text-gray-600">
                                                <Users className="h-4 w-4 mr-2" />
                                                <span className="text-sm">Capacity: {danceClass.capacity}</span>
                                            </div>
                                            {danceClass.comment && (
                                                <div className="flex items-start text-gray-600">
                                                    <span className="text-sm italic">"{danceClass.comment}"</span>
                                                </div>
                                            )}
                                        </div>

                                        <div className="flex space-x-2 pt-3 border-t border-gray-200">
                                            <button
                                                className="btn-secondary text-sm px-3 py-1 flex items-center space-x-1"
                                                onClick={() => onEditClass(danceClass)}
                                            >
                                                <Edit className="h-3 w-3" />
                                                <span>Edit</span>
                                            </button>
                                            <button
                                                className="btn-danger text-sm px-3 py-1 flex items-center space-x-1"
                                                onClick={() => onDeleteClass(danceClass.id)}
                                            >
                                                <Trash2 className="h-3 w-3" />
                                                <span>Delete</span>
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                );
            })}
        </div>
    );
}; 