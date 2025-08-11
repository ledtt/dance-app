import React, { useState, useMemo } from 'react';
import { Navigation } from '@/components/layout/Navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useQuery } from 'react-query';
import { apiClient } from '@/api/client';
import { ScheduleCard } from '@/components/schedule/ScheduleCard';
import { ScheduleFilters } from '@/components/schedule/ScheduleFilters';
import { BookingModal } from '@/components/booking/BookingModal';
import { DanceClass } from '@/types';
import { Calendar } from 'lucide-react';

export const SchedulePage: React.FC = () => {
  const { user } = useAuth();
  const [filters, setFilters] = useState({
    teacher: '',
    weekday: '',
    name: '',
    is_active: 'true',
  });
  const [selectedClass, setSelectedClass] = useState<DanceClass | null>(null);
  const [isBookingModalOpen, setIsBookingModalOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string>('');

  // Мемоизируем параметры запроса, чтобы избежать лишних перезапросов
  const queryParams = useMemo(() => {
    const params = {
      teacher: filters.teacher || undefined,
      weekday: filters.weekday ? parseInt(filters.weekday) : undefined,
      name: filters.name || undefined,
      is_active: filters.is_active ? filters.is_active === 'true' : undefined,
    };

    // Убираем undefined значения для стабильности
    const cleanParams = Object.fromEntries(
      Object.entries(params).filter(([_, value]) => value !== undefined)
    );

    return cleanParams;
  }, [filters.teacher, filters.weekday, filters.name, filters.is_active]);

  const { data: scheduleData, isLoading, error, refetch } = useQuery(
    ['schedule', queryParams],
    () => apiClient.getSchedule(queryParams),
    {
      retry: 1,
      staleTime: 30000, // Кэшируем данные на 30 секунд
      cacheTime: 60000, // Храним в кэше 1 минуту
      onError: (error) => {
        console.error('Schedule query error:', error);
        if (error instanceof Error) {
          setErrorMessage(error.message);
        } else {
          setErrorMessage('An error occurred while loading the schedule');
        }
      },
    }
  );

  // Отдельный запрос для получения всех преподавателей (независимо от фильтров)
  const { data: allTeachersData } = useQuery(
    'allTeachers',
    () => apiClient.getSchedule({}), // Пустые параметры = все классы
    {
      retry: 1,
      staleTime: 300000, // Кэшируем на 5 минут
      cacheTime: 600000, // Храним в кэше 10 минут
      onError: (error) => {
        console.error('All teachers query error:', error);
      },
    }
  );

  const { data: myBookings } = useQuery(
    'myBookings',
    () => apiClient.getMyBookings(),
    {
      retry: 1,
      staleTime: 30000, // Cache data for 30 seconds
      cacheTime: 60000, // Keep in cache for 1 minute
      onError: (error) => {
        console.error('Bookings query error:', error);
      },
    }
  );

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleClearFilters = () => {
    setFilters({
      teacher: '',
      weekday: '',
      name: '',
      is_active: 'true',
    });
  };

  const handleBook = (danceClass: DanceClass) => {
    setSelectedClass(danceClass);
    setIsBookingModalOpen(true);
  };

  const handleBookingSuccess = () => {
    console.log('Booking successful, refetching data...');
    refetch(); // Reload schedule data
    // You can also add invalidateQueries for myBookings
    // queryClient.invalidateQueries('myBookings');
  };

  const isClassBooked = (classId: string) => {
    return myBookings?.some(booking => booking.class_id === classId) || false;
  };

  // Extract unique teachers for filter from all data (not filtered)
  const teachers = Array.from(
    new Set(allTeachersData?.items?.map((classItem: any) => classItem.teacher) || [])
  ).sort();

  // Enhanced debug logs
  console.log('SchedulePage render:', {
    isLoading,
    error,
    scheduleDataType: typeof scheduleData,
    scheduleDataItemsType: typeof scheduleData?.items,
    scheduleDataItemsLength: Array.isArray(scheduleData?.items) ? scheduleData.items.length : 'not array',
    scheduleDataRaw: scheduleData,
    user,
    queryParams,
  });

  // Safe data extraction
  const scheduleItems = scheduleData?.items || [];
  const isScheduleDataValid = Array.isArray(scheduleItems) && scheduleItems.length > 0;
  const hasActiveFilters = Object.values(filters).some(value => value !== '');

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Dance Schedule</h1>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Choose and book the classes that interest you
          </p>
        </div>

        {/* Error Display */}
        {errorMessage && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">
                  Error loading schedule
                </h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{errorMessage}</p>
                </div>
                <div className="mt-4">
                  <button
                    onClick={() => {
                      setErrorMessage('');
                      refetch();
                    }}
                    className="bg-red-100 text-red-800 px-3 py-2 rounded-md text-sm font-medium hover:bg-red-200"
                  >
                    Try again
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Filters */}
        <ScheduleFilters
          filters={filters}
          onFilterChange={handleFilterChange}
          onClearFilters={handleClearFilters}
          teachers={teachers}
        />

        {/* Schedule Grid */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          </div>
        ) : isScheduleDataValid ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {scheduleItems.map((danceClass) => (
              <ScheduleCard
                key={danceClass.id}
                danceClass={danceClass}
                onBook={handleBook}
                isBooked={isClassBooked(danceClass.id)}
                isAdmin={user?.role === 'admin'}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {error ? 'Error loading schedule' : 'No classes found'}
            </h3>
            <p className="text-gray-600 mb-4">
              {error
                ? 'An error occurred while loading data. Please refresh the page.'
                : hasActiveFilters
                  ? 'Try changing filters or contact administrator'
                  : 'No classes are available at the moment. Please contact administrator.'
              }
            </p>
            {hasActiveFilters && (
              <button
                onClick={handleClearFilters}
                className="btn-secondary"
              >
                Clear filters
              </button>
            )}
          </div>
        )}

        {/* Pagination */}
        {scheduleData && scheduleData.pages > 1 && (
          <div className="flex items-center justify-center mt-8">
            <div className="flex space-x-2">
              {Array.from({ length: scheduleData.pages }, (_, i) => (
                <button
                  key={i}
                  className={`px-3 py-2 rounded-lg text-sm font-medium ${scheduleData.page === i + 1
                    ? 'bg-primary-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                    }`}
                >
                  {i + 1}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Booking Modal */}
      {selectedClass && (
        <BookingModal
          danceClass={selectedClass}
          isOpen={isBookingModalOpen}
          onClose={() => {
            setIsBookingModalOpen(false);
            setSelectedClass(null);
          }}
          onSuccess={handleBookingSuccess}
        />
      )}
    </div>
  );
}; 