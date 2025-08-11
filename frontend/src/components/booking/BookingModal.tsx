import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { DanceClass } from '@/types';
import { WEEKDAYS } from '@/types';
import { X, Calendar, Clock, User, Users } from 'lucide-react';
import { format, addDays, startOfToday } from 'date-fns';
import { apiClient } from '@/api/client';
import toast from 'react-hot-toast';

interface BookingModalProps {
    danceClass: DanceClass;
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
}

interface BookingFormData {
    date: string;
}

export const BookingModal: React.FC<BookingModalProps> = ({
    danceClass,
    isOpen,
    onClose,
    onSuccess,
}) => {
    const [isLoading, setIsLoading] = useState(false);

    const {
        register,
        handleSubmit,
        formState: { errors },
        watch,
    } = useForm<BookingFormData>();

    const selectedDate = watch('date');

    const getWeekdayName = (weekday: number) => {
        return WEEKDAYS[weekday as keyof typeof WEEKDAYS] || 'Unknown';
    };

    const formatTime = (time: string) => {
        return time ? time.substring(0, 5) : 'N/A';
    };

    // Generate available dates for the next 4 weeks
    const generateAvailableDates = () => {
        const dates = [];
        const today = startOfToday();

        for (let i = 0; i < 28; i++) {
            const date = addDays(today, i);
            if (date.getDay() === danceClass.weekday) {
                dates.push(date);
            }
        }

        return dates;
    };

    const availableDates = generateAvailableDates();

    const onSubmit = async (data: BookingFormData) => {
        setIsLoading(true);
        try {
            await apiClient.createBooking({
                class_id: danceClass.id,
                date: data.date,
            });
            toast.success('Class successfully booked!');
            onSuccess();
            onClose();
        } catch (error) {
            // Error is handled by the API client
        } finally {
            setIsLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
                <div className="p-6">
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-2xl font-bold text-gray-900">Book Class</h2>
                        <button
                            onClick={onClose}
                            className="text-gray-400 hover:text-gray-600"
                        >
                            <X className="h-6 w-6" />
                        </button>
                    </div>

                    {/* Class Info */}
                    <div className="card mb-6">
                        <h3 className="text-xl font-semibold text-gray-900 mb-3">
                            {danceClass.name}
                        </h3>

                        <div className="space-y-2">
                            <div className="flex items-center text-gray-600">
                                <User className="h-4 w-4 mr-2" />
                                <span className="text-sm">Teacher: {danceClass.teacher}</span>
                            </div>

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
                    </div>

                    {/* Booking Form */}
                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Select Date
                            </label>
                            <select
                                {...register('date', {
                                    required: 'Please select a date',
                                })}
                                className="input-field"
                            >
                                <option value="">Select date...</option>
                                {availableDates.map((date) => (
                                    <option key={date.toISOString()} value={format(date, 'yyyy-MM-dd')}>
                                        {format(date, 'EEEE, MMMM d, yyyy')}
                                    </option>
                                ))}
                            </select>
                            {errors.date && (
                                <p className="mt-1 text-sm text-red-600">{errors.date.message}</p>
                            )}
                        </div>

                        {selectedDate && (
                            <div className="p-4 bg-blue-50 rounded-lg">
                                <p className="text-sm text-blue-800">
                                    You selected: {format(new Date(selectedDate), 'EEEE, MMMM d, yyyy')}
                                </p>
                            </div>
                        )}

                        <div className="flex space-x-3 pt-4">
                            <button
                                type="button"
                                onClick={onClose}
                                className="btn-secondary flex-1"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                disabled={isLoading || !selectedDate}
                                className="btn-primary flex-1"
                            >
                                {isLoading ? (
                                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                                ) : (
                                    'Book'
                                )}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}; 