import React from 'react';
import { Navigation } from '@/components/layout/Navigation';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/api/client';
import { Booking } from '@/types';
import {
  Calendar,
  Clock,
  User,
  Trash2,
  BookOpen
} from 'lucide-react';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

export const BookingsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const { data: bookings, isLoading } = useQuery('myBookings', () =>
    apiClient.getMyBookings()
  );

  const cancelBookingMutation = useMutation(
    (bookingId: string) => apiClient.cancelBooking(bookingId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('myBookings');
        queryClient.invalidateQueries('todaySchedule');
        toast.success('Booking cancelled');
      },
      onError: () => {
        toast.error('Error cancelling booking');
      },
    }
  );

  const handleCancelBooking = (booking: Booking) => {
    if (window.confirm('Are you sure you want to cancel this booking?')) {
      cancelBookingMutation.mutate(booking.id);
    }
  };



  const formatTime = (time: string) => {
    return time ? time.substring(0, 5) : 'N/A';
  };

  const isUpcoming = (booking: Booking) => {
    const now = new Date();
    const bookingDate = new Date(booking.date);

    // Если дата записи в будущем - это upcoming
    if (bookingDate > now) {
      return true;
    }

    // Если дата записи сегодня, проверяем время занятия
    if (bookingDate.toDateString() === now.toDateString()) {
      if (booking.class_info?.start_time) {
        const [hours, minutes] = booking.class_info.start_time.split(':').map(Number);
        const classTime = new Date();
        classTime.setHours(hours, minutes, 0, 0);
        return now < classTime; // Если время занятия еще не наступило - это upcoming
      }
    }

    return false;
  };

  const isToday = (booking: Booking) => {
    const now = new Date();
    const bookingDate = new Date(booking.date);
    return bookingDate.toDateString() === now.toDateString();
  };

  const upcomingBookings = bookings?.filter(booking => isUpcoming(booking)) || [];
  const pastBookings = bookings?.filter(booking => !isUpcoming(booking)) || [];

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">My bookings</h1>
          <p className="text-gray-600">
            Manage your class bookings
          </p>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          </div>
        ) : bookings && bookings.length > 0 ? (
          <div className="space-y-8">
            {/* Upcoming Bookings */}
            {upcomingBookings.length > 0 && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                  <BookOpen className="h-5 w-5 mr-2" />
                  Upcoming classes ({upcomingBookings.length})
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {upcomingBookings.map((booking) => (
                    <div key={booking.id} className="card">
                      <div className="flex items-start justify-between mb-4">
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">
                            {booking.class_info?.name || 'Class'}
                          </h3>
                          <div className="flex items-center text-gray-600 mt-1">
                            <User className="h-4 w-4 mr-1" />
                            <span className="text-sm">{booking.class_info?.teacher}</span>
                          </div>
                        </div>
                        {!isToday(booking) && (
                          <button
                            onClick={() => handleCancelBooking(booking)}
                            disabled={cancelBookingMutation.isLoading}
                            className="btn-danger btn-sm flex items-center space-x-1"
                            title="Cancel booking"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                      </div>

                      <div className="space-y-2 mb-4">
                        <div className="flex items-center text-gray-600">
                          <Calendar className="h-4 w-4 mr-2" />
                          <span className="text-sm">
                            {format(new Date(booking.date), 'EEEE, d MMMM yyyy')}
                          </span>
                        </div>

                        <div className="flex items-center text-gray-600">
                          <Clock className="h-4 w-4 mr-2" />
                          <span className="text-sm">
                            {booking.class_info?.start_time ? formatTime(booking.class_info.start_time) : 'Time not specified'}
                          </span>
                        </div>
                      </div>

                      <div className="pt-4 border-t border-gray-200">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          Confirmed
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Past Bookings */}
            {pastBookings.length > 0 && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                  <Calendar className="h-5 w-5 mr-2" />
                  Past classes ({pastBookings.length})
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {pastBookings.map((booking) => (
                    <div key={booking.id} className="card opacity-75">
                      <div className="mb-4">
                        <h3 className="text-lg font-semibold text-gray-900">
                          {booking.class_info?.name || 'Class'}
                        </h3>
                        <div className="flex items-center text-gray-600 mt-1">
                          <User className="h-4 w-4 mr-1" />
                          <span className="text-sm">{booking.class_info?.teacher}</span>
                        </div>
                      </div>

                      <div className="space-y-2 mb-4">
                        <div className="flex items-center text-gray-600">
                          <Calendar className="h-4 w-4 mr-2" />
                          <span className="text-sm">
                            {format(new Date(booking.date), 'EEEE, d MMMM yyyy')}
                          </span>
                        </div>

                        <div className="flex items-center text-gray-600">
                          <Clock className="h-4 w-4 mr-2" />
                          <span className="text-sm">
                            {booking.class_info?.start_time ? formatTime(booking.class_info.start_time) : 'Time not specified'}
                          </span>
                        </div>
                      </div>

                      <div className="pt-4 border-t border-gray-200">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          Completed
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-12">
            <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              You have no bookings yet
            </h3>
            <p className="text-gray-600 mb-6">
              Book your first class in the "Schedule" section
            </p>
            <button className="btn-primary" onClick={() => navigate('/schedule')}>
              View schedule
            </button>
          </div>
        )}

        {/* Statistics */}
        {bookings && bookings.length > 0 && (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="card text-center">
              <div className="text-2xl font-bold text-primary-600 mb-1">
                {bookings.length}
              </div>
              <div className="text-sm text-gray-600">Total bookings</div>
            </div>

            <div className="card text-center">
              <div className="text-2xl font-bold text-green-600 mb-1">
                {upcomingBookings.length}
              </div>
              <div className="text-sm text-gray-600">Upcoming</div>
            </div>

            <div className="card text-center">
              <div className="text-2xl font-bold text-gray-600 mb-1">
                {pastBookings.length}
              </div>
              <div className="text-sm text-gray-600">Completed</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}; 