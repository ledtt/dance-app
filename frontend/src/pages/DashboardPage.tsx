import React, { useState } from 'react';
import { Navigation } from '@/components/layout/Navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { apiClient } from '@/api/client';
import {
  Calendar,
  Users,
  Clock,
  Music,
  User,
  AlertTriangle
} from 'lucide-react';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [showBookingModal, setShowBookingModal] = useState(false);
  const [selectedClass, setSelectedClass] = useState<any>(null);

  const { data: myBookings } = useQuery('myBookings', () =>
    apiClient.getMyBookings()
  );

  const { data: todaySchedule, isLoading: scheduleLoading } = useQuery('todaySchedule', () =>
    apiClient.getSchedule({ is_active: true })
  );

  const createBookingMutation = useMutation(
    (bookingData: { class_id: string; date: string }) => apiClient.createBooking(bookingData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('myBookings');
        queryClient.invalidateQueries('todaySchedule');
        toast.success('Successfully booked the class!');
        setShowBookingModal(false);
        setSelectedClass(null);
      },
      onError: (error: any) => {
        const message = error.response?.data?.detail || 'Error booking the class';
        toast.error(message);
      },
    }
  );

  // Get today's weekday (0 = Sunday, 1 = Monday, etc.)
  const today = new Date();
  const todayWeekday = today.getDay();
  const adjustedWeekday = todayWeekday === 0 ? 7 : todayWeekday; // Convert Sunday from 0 to 7

  // Filter today's classes
  const todaysClasses = todaySchedule?.items?.filter((danceClass: any) =>
    danceClass.weekday === adjustedWeekday
  ) || [];

  // Check if user is booked for each class
  const isClassBooked = (classId: string) => {
    return myBookings?.some(booking => booking.class_id === classId) || false;
  };

  // Check if class has available spots
  const getAvailableSpots = (danceClass: any) => {
    const bookedCount = myBookings?.filter(booking => booking.class_id === danceClass.id).length || 0;
    return Math.max(0, danceClass.capacity - bookedCount);
  };

  // Check if class has started
  const isClassStarted = (startTime: string) => {
    const now = new Date();
    const [hours, minutes] = startTime.split(':').map(Number);
    const classTime = new Date();
    classTime.setHours(hours, minutes, 0, 0);
    return now > classTime;
  };

  const handleBookClass = (danceClass: any) => {
    // Prevent booking for admin users
    if (user?.role === 'admin') {
      return;
    }
    setSelectedClass(danceClass);
    setShowBookingModal(true);
  };

  const confirmBooking = () => {
    if (!selectedClass) return;

    const today = new Date();
    const formattedDate = format(today, 'yyyy-MM-dd');

    createBookingMutation.mutate({
      class_id: selectedClass.id,
      date: formattedDate
    });
  };

  // Get unique dance styles and teachers
  const danceStyles = Array.from(
    new Set(todaySchedule?.items?.map((classItem: any) => classItem.name) || [])
  );

  const teachers = Array.from(
    new Set(todaySchedule?.items?.map((classItem: any) => classItem.teacher) || [])
  );

  const stats = [
    {
      title: 'Dance Styles',
      value: danceStyles.length,
      icon: Music,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      title: 'Teachers',
      value: teachers.length,
      icon: Users,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
  ];

  const formatTime = (time: string) => {
    return time ? time.substring(0, 5) : 'N/A';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome, {user?.name}! 👋
          </h1>
          <p className="text-gray-600">
            Today is {format(new Date(), 'EEEE, MMMM d, yyyy')}
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {stats.map((stat) => {
            const Icon = stat.icon;
            return (
              <div key={stat.title} className="card">
                <div className="flex items-center">
                  <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                    <Icon className={`h-6 w-6 ${stat.color}`} />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                    <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Today's Schedule */}
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900">Today's Schedule</h2>
            <Calendar className="h-5 w-5 text-gray-400" />
          </div>

          {scheduleLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
          ) : todaysClasses.length > 0 ? (
            <div className="space-y-4">
              {todaysClasses.map((danceClass: any) => {
                const isBooked = isClassBooked(danceClass.id);
                const availableSpots = getAvailableSpots(danceClass);
                const hasStarted = isClassStarted(danceClass.start_time);
                const canBook = !isBooked && availableSpots > 0 && !hasStarted;

                return (
                  <div
                    key={danceClass.id}
                    className={`flex items-center justify-between p-4 rounded-lg ${isBooked
                      ? 'bg-green-50 border border-green-200'
                      : availableSpots === 0
                        ? 'bg-red-50 border border-red-200'
                        : hasStarted
                          ? 'bg-gray-50 border border-gray-200 opacity-75'
                          : 'bg-gray-50 border border-gray-200'
                      }`}
                  >
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-medium text-gray-900">{danceClass.name}</h3>
                        <div className="flex items-center space-x-2">
                          {isBooked && (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                              Booked
                            </span>
                          )}
                          {availableSpots === 0 && !isBooked && (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                              Full
                            </span>
                          )}
                          {hasStarted && (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                              Started
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center text-gray-600 mb-1">
                        <User className="h-4 w-4 mr-1" />
                        <span className="text-sm">{danceClass.teacher}</span>
                      </div>
                      <div className="flex items-center text-gray-600 mt-1">
                        <Users className="h-4 w-4 mr-1" />
                        <span className="text-sm">
                          {availableSpots > 0 ? (
                            <span className="text-green-600 font-medium">
                              {availableSpots} spots available
                            </span>
                          ) : (
                            <span className="text-red-600 font-medium">
                              No spots available
                            </span>
                          )}
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">
                        {formatTime(danceClass.start_time)}
                      </p>
                      <p className="text-xs text-gray-500">
                        {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][danceClass.weekday - 1]}
                      </p>
                      {canBook && user?.role !== 'admin' && (
                        <button
                          onClick={() => handleBookClass(danceClass)}
                          disabled={createBookingMutation.isLoading}
                          className="mt-2 btn-primary btn-sm"
                        >
                          Book Now
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-8">
              <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No classes today</h3>
              <p className="text-gray-600">Check the schedule for other days</p>
            </div>
          )}
        </div>
      </div>

      {/* Booking Confirmation Modal */}
      {showBookingModal && selectedClass && user?.role !== 'admin' && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <div className="flex items-center mb-4">
              <AlertTriangle className="h-6 w-6 text-yellow-500 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900">Confirm Booking</h3>
            </div>
            <p className="text-gray-600 mb-4">
              Are you sure you want to book <strong>{selectedClass.name}</strong> with {selectedClass.teacher}?
            </p>
            <p className="text-sm text-red-600 mb-6">
              ⚠️ Important: Once booked, this class cannot be cancelled.
            </p>
            <div className="flex space-x-3">
              <button
                onClick={() => {
                  setShowBookingModal(false);
                  setSelectedClass(null);
                }}
                className="flex-1 btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={confirmBooking}
                disabled={createBookingMutation.isLoading}
                className="flex-1 btn-primary"
              >
                {createBookingMutation.isLoading ? 'Booking...' : 'Confirm Booking'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}; 