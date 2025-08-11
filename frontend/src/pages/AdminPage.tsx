import React, { useState } from 'react';
import { Navigation } from '@/components/layout/Navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { apiClient } from '@/api/client';
import {
  TrendingUp,
  Users,
  Calendar,
  BookOpen,
  Plus,
  BarChart3,
  Clock,
  Edit,
  Trash2,
  User,
  Shield,
  UserCheck
} from 'lucide-react';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import toast from 'react-hot-toast';
import { ClassesByDay } from '@/components/admin/ClassesByDay';
import { BookingFilters, BookingFilters as BookingFiltersType } from '@/components/admin/BookingFilters';
import { UserDetails } from '@/components/admin/UserDetails';

interface ClassFormData {
  name: string;
  teacher: string;
  weekday: number;
  start_time: string;
  capacity: number;
  comment?: string;
  active: boolean;
}

export const AdminPage: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const [activeTab, setActiveTab] = useState<'overview' | 'classes' | 'bookings' | 'users'>('overview');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingClass, setEditingClass] = useState<any>(null);
  const [bookingFilters, setBookingFilters] = useState<BookingFiltersType>({});
  const [selectedUser, setSelectedUser] = useState<any>(null);
  const [showUserDetails, setShowUserDetails] = useState(false);
  const [userBookings, setUserBookings] = useState<any[]>([]);
  const [formData, setFormData] = useState<ClassFormData>({
    name: '',
    teacher: '',
    weekday: 1,
    start_time: '18:00',
    capacity: 20,
    comment: '',
    active: true
  });

  const queryClient = useQueryClient();

  const { data: scheduleStats } = useQuery('scheduleStats', () =>
    apiClient.getScheduleStatistics()
  );

  const { data: bookingStats } = useQuery('bookingStats', () =>
    apiClient.getBookingStatistics()
  );

  const { data: allBookings } = useQuery(
    ['allBookings', bookingFilters],
    () => apiClient.getAllBookings({
      date_from: bookingFilters.startDate,
      date_to: bookingFilters.endDate,
      user_id: bookingFilters.userId,
      teacher: bookingFilters.teacher,
      class_name: bookingFilters.className,
    }),
    {
      keepPreviousData: true,
      onSuccess: (data) => {
        console.log('AdminPage - allBookings data:', data);
        console.log('AdminPage - allBookings items:', data?.items);
        if (data?.items && data.items.length > 0) {
          console.log('AdminPage - First booking:', data.items[0]);
          console.log('AdminPage - First booking user:', data.items[0]?.user);
          console.log('AdminPage - First booking class_info:', data.items[0]?.class_info);
        }
      },
    }
  );

  const { data: scheduleData } = useQuery('schedule', () =>
    apiClient.getSchedule({ size: 200 }), // Увеличиваем лимит
    {
      onSuccess: (data) => {
        console.log('AdminPage - scheduleData:', data);
        if (data?.items) {
          console.log('AdminPage - schedule items count:', data.items.length);
          // Группируем по дням недели для отладки
          const byWeekday = data.items.reduce((acc: any, item: any) => {
            const day = item.weekday;
            if (!acc[day]) acc[day] = [];
            acc[day].push(item);
            return acc;
          }, {});
          console.log('AdminPage - classes by weekday:', byWeekday);
        }
      }
    }
  );

  const { data: allUsers } = useQuery('allUsers', () =>
    apiClient.getAllUsers()
  );

  // Mutations
  const createClassMutation = useMutation(
    (data: ClassFormData) => apiClient.createClass(data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('schedule');
        queryClient.invalidateQueries('scheduleStats');
        setShowAddModal(false);
        setFormData({
          name: '',
          teacher: '',
          weekday: 1,
          start_time: '18:00',
          capacity: 20,
          comment: '',
          active: true
        });
        toast.success('Class created successfully');
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to create class');
      }
    }
  );

  const updateClassMutation = useMutation(
    ({ id, data }: { id: string; data: ClassFormData }) =>
      apiClient.updateClass(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('schedule');
        queryClient.invalidateQueries('scheduleStats');
        setShowEditModal(false);
        setEditingClass(null);
        setFormData({
          name: '',
          teacher: '',
          weekday: 1,
          start_time: '18:00',
          capacity: 20,
          comment: '',
          active: true
        });
        toast.success('Class updated successfully');
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to update class');
      }
    }
  );

  const deleteClassMutation = useMutation(
    (id: string) => apiClient.deleteClass(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('schedule');
        queryClient.invalidateQueries('scheduleStats');
        toast.success('Class deleted successfully');
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to delete class');
      }
    }
  );

  const updateUserRoleMutation = useMutation(
    ({ userId, role }: { userId: string; role: 'user' | 'admin' }) =>
      apiClient.updateUserRole(userId, role),
    {
      onSuccess: async () => {
        queryClient.invalidateQueries('allUsers');
        queryClient.invalidateQueries('me'); // Also refresh current user data
        await refreshUser(); // Refresh current user data immediately
        toast.success('User role updated successfully');
      },
      onError: (error: any) => {
        const errorMessage = error.response?.data?.detail || 'Failed to update user role';
        toast.error(errorMessage);

        // If the error is about removing the last admin, show a more specific message
        if (errorMessage.includes('last administrator')) {
          toast.error('Cannot remove the last administrator from the system');
        } else if (errorMessage.includes('your own admin privileges')) {
          toast.error('You cannot remove your own admin privileges');
        }
      }
    }
  );

  const handleAddClass = () => {
    setShowAddModal(true);
  };

  const handleEditClass = (danceClass: any) => {
    setEditingClass(danceClass);
    setFormData({
      name: danceClass.name,
      teacher: danceClass.teacher,
      weekday: danceClass.weekday,
      start_time: danceClass.start_time ? danceClass.start_time.substring(0, 5) : '18:00',
      capacity: danceClass.capacity,
      comment: danceClass.comment || '',
      active: danceClass.active
    });
    setShowEditModal(true);
  };

  const handleDeleteClass = (id: string) => {
    if (window.confirm('Are you sure you want to delete this class?')) {
      deleteClassMutation.mutate(id);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (showEditModal && editingClass) {
      updateClassMutation.mutate({ id: editingClass.id, data: formData });
    } else {
      createClassMutation.mutate(formData);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseInt(value) : type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    }));
  };

  const handleBookingFiltersChange = (filters: BookingFiltersType) => {
    setBookingFilters(filters);
    // Фильтры автоматически обновят запрос благодаря зависимости в useQuery
  };

  const handleUserClick = (user: any) => {
    // Фильтруем бронирования для конкретного пользователя
    const userBookings = allBookings?.items?.filter((booking: any) =>
      booking.user?.id === user.id || booking.user_id === user.id
    ) || [];

    console.log('UserDetails - User:', user);
    console.log('UserDetails - User ID:', user.id);
    console.log('UserDetails - All bookings:', allBookings?.items);
    console.log('UserDetails - Filtered bookings:', userBookings);

    setSelectedUser(user);
    setUserBookings(userBookings);
    setShowUserDetails(true);
  };

  const handleBookClassForUser = (userId: string) => {
    // Here you would implement the booking functionality
    toast.success('Booking functionality will be implemented');
  };

  const handleEditUser = (user: any) => {
    // TODO: Implement edit user functionality
    console.log('Edit user:', user);
    toast.success('Edit user functionality will be implemented soon');
  };

  const handleDeactivateUser = (userId: string) => {
    // TODO: Implement deactivate user functionality
    console.log('Deactivate user:', userId);
    toast.success('Deactivate user functionality will be implemented soon');
  };

  const handleRoleChange = (userId: string, currentRole: string) => {
    const newRole = currentRole === 'admin' ? 'user' : 'admin';
    const action = newRole === 'admin' ? 'make admin' : 'remove admin privileges';
    const userAction = newRole === 'admin' ? 'grant admin privileges to' : 'remove admin privileges from';

    if (window.confirm(`Are you sure you want to ${userAction} this user?`)) {
      updateUserRoleMutation.mutate({ userId, role: newRole as 'user' | 'admin' });
    }
  };

  // Redirect if not admin
  if (user?.role !== 'admin') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Access denied</h1>
          <p className="text-gray-600">You do not have permission to access the admin panel</p>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'classes', label: 'Classes', icon: Calendar },
    { id: 'bookings', label: 'Bookings', icon: BookOpen },
    { id: 'users', label: 'Users', icon: Users },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Admin panel</h1>
          <p className="text-gray-600">
            Manage classes, bookings, and statistics
          </p>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-8">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="space-y-8">
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="card">
                <div className="flex items-center">
                  <div className="p-3 rounded-lg bg-blue-100">
                    <Calendar className="h-6 w-6 text-blue-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total classes</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {scheduleStats?.total_classes || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="card">
                <div className="flex items-center">
                  <div className="p-3 rounded-lg bg-green-100">
                    <TrendingUp className="h-6 w-6 text-green-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Active classes</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {scheduleStats?.active_classes || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="card">
                <div className="flex items-center">
                  <div className="p-3 rounded-lg bg-purple-100">
                    <Users className="h-6 w-6 text-purple-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Teachers</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {scheduleStats?.total_teachers || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="card">
                <div className="flex items-center">
                  <div className="p-3 rounded-lg bg-orange-100">
                    <BookOpen className="h-6 w-6 text-orange-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total bookings</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {bookingStats?.total_bookings || 0}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Booking Statistics */}
            {bookingStats && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="card">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Booking statistics
                  </h3>
                  <div className="space-y-4">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Bookings today:</span>
                      <span className="font-semibold">{bookingStats.bookings_today}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Bookings this week:</span>
                      <span className="font-semibold">{bookingStats.bookings_this_week}</span>
                    </div>
                    {bookingStats.most_popular_class && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Most popular class:</span>
                        <span className="font-semibold">{bookingStats.most_popular_class.name}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="card">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Classes by day of the week
                  </h3>
                  <div className="space-y-3">
                    {scheduleStats?.classes_by_weekday &&
                      scheduleStats.classes_by_weekday.map((item) => (
                        <div key={item.weekday} className="flex justify-between">
                          <span className="text-gray-600">
                            {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][item.weekday - 1]}:
                          </span>
                          <span className="font-semibold">{item.count}</span>
                        </div>
                      ))
                    }
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'classes' && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">Manage classes</h2>
              <button
                className="btn-primary flex items-center space-x-2"
                onClick={handleAddClass}
              >
                <Plus className="h-4 w-4" />
                <span>Add class</span>
              </button>
            </div>

            {scheduleData?.items && scheduleData.items.length > 0 ? (
              <ClassesByDay
                classes={scheduleData.items}
                onEditClass={handleEditClass}
                onDeleteClass={handleDeleteClass}
              />
            ) : (
              <div className="text-center py-12">
                <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No classes
                </h3>
                <p className="text-gray-600">
                  Create your first class to start working
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'bookings' && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">All bookings</h2>
              <div className="flex space-x-2">
                <button className="btn-secondary">Export</button>
              </div>
            </div>

            <BookingFilters
              onFiltersChange={handleBookingFiltersChange}
              users={allUsers?.items || []}
              teachers={scheduleData?.items?.map((c: any) => c.teacher).filter((v: any, i: any, a: any) => a.indexOf(v) === i) || []}
              classNames={scheduleData?.items?.map((c: any) => c.name).filter((v: any, i: any, a: any) => a.indexOf(v) === i) || []}
            />

            {allBookings?.items && allBookings.items.length > 0 ? (
              <div className="card">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          User
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Class
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Teacher
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Date
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Time
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {allBookings.items.map((booking) => {
                        // Debug logging
                        console.log('Booking data:', booking);
                        console.log('User data:', booking.user);
                        console.log('Class info:', booking.class_info);

                        return (
                          <tr key={booking.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm font-medium text-gray-900">
                                {booking.user?.name || 'Unknown User'}
                              </div>
                              <div className="text-sm text-gray-500">
                                {booking.user?.email || 'unknown@example.com'}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm font-medium text-gray-900">
                                {booking.class_info?.name || 'Archived/Deleted Class'}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm text-gray-900">
                                {booking.class_info?.teacher || 'Unknown Teacher'}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {format(new Date(booking.date), 'd MMMM yyyy', { locale: ru })}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {booking.class_info?.start_time ?
                                format(new Date(`2000-01-01T${booking.class_info.start_time}`), 'HH:mm') :
                                'Unknown'
                              }
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                Confirmed
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No bookings found
                </h3>
                <p className="text-gray-600">
                  {bookingFilters && Object.keys(bookingFilters).length > 0
                    ? 'Try adjusting your filters'
                    : 'No bookings have been made yet'
                  }
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'users' && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">Manage users</h2>
              <div className="flex space-x-2">
                <button className="btn-secondary">Export</button>
                <button className="btn-primary">Filters</button>
              </div>
            </div>

            {allUsers?.items && allUsers.items.length > 0 ? (
              <div className="card">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          User
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Role
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Created
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {allUsers?.items?.map((user) => (
                        <tr key={user.id}>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">
                              {user.name}
                            </div>
                            <div className="text-sm text-gray-500">
                              {user.email}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${user.role === 'admin'
                              ? 'bg-purple-100 text-purple-800'
                              : 'bg-gray-100 text-gray-800'
                              }`}>
                              {user.role}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${user.is_active
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                              }`}>
                              {user.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {format(new Date(user.created_at), 'd MMM yyyy', { locale: ru })}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <div className="flex space-x-2">
                              <button
                                onClick={() => handleUserClick(user)}
                                className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors duration-200"
                              >
                                <User className="h-4 w-4 mr-1" />
                                View
                              </button>
                              <button
                                onClick={() => handleRoleChange(user.id, user.role)}
                                disabled={updateUserRoleMutation.isLoading}
                                className={`inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md transition-colors duration-200 ${user.role === 'admin'
                                  ? 'text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500'
                                  : 'text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500'
                                  }`}
                              >
                                {user.role === 'admin' ? (
                                  <>
                                    <UserCheck className="h-4 w-4 mr-1" />
                                    Remove Admin
                                  </>
                                ) : (
                                  <>
                                    <Shield className="h-4 w-4 mr-1" />
                                    Make Admin
                                  </>
                                )}
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No users
                </h3>
                <p className="text-gray-600">
                  No users found in the system
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Add Class Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-semibold mb-4">Add New Class</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Class Name</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Teacher</label>
                <input
                  type="text"
                  name="teacher"
                  value={formData.teacher}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Weekday</label>
                <select
                  name="weekday"
                  value={formData.weekday}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value={1}>Monday</option>
                  <option value={2}>Tuesday</option>
                  <option value={3}>Wednesday</option>
                  <option value={4}>Thursday</option>
                  <option value={5}>Friday</option>
                  <option value={6}>Saturday</option>
                  <option value={7}>Sunday</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Start Time</label>
                <input
                  type="time"
                  name="start_time"
                  value={formData.start_time}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Capacity</label>
                <input
                  type="number"
                  name="capacity"
                  value={formData.capacity}
                  onChange={handleInputChange}
                  min="1"
                  max="100"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  required
                />
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  name="active"
                  checked={formData.active}
                  onChange={handleInputChange}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <label className="ml-2 block text-sm text-gray-900">Active</label>
              </div>
              <div className="flex space-x-3 pt-4">
                <button
                  type="submit"
                  className="btn-primary flex-1"
                  disabled={createClassMutation.isLoading}
                >
                  {createClassMutation.isLoading ? 'Creating...' : 'Create Class'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Class Modal */}
      {showEditModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-semibold mb-4">Edit Class</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Class Name</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Teacher</label>
                <input
                  type="text"
                  name="teacher"
                  value={formData.teacher}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Weekday</label>
                <select
                  name="weekday"
                  value={formData.weekday}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value={1}>Monday</option>
                  <option value={2}>Tuesday</option>
                  <option value={3}>Wednesday</option>
                  <option value={4}>Thursday</option>
                  <option value={5}>Friday</option>
                  <option value={6}>Saturday</option>
                  <option value={7}>Sunday</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Start Time</label>
                <input
                  type="time"
                  name="start_time"
                  value={formData.start_time}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Capacity</label>
                <input
                  type="number"
                  name="capacity"
                  value={formData.capacity}
                  onChange={handleInputChange}
                  min="1"
                  max="100"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Comment</label>
                <textarea
                  name="comment"
                  value={formData.comment}
                  onChange={handleInputChange}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Optional comment about the class..."
                />
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  name="active"
                  checked={formData.active}
                  onChange={handleInputChange}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <label className="ml-2 block text-sm text-gray-900">Active</label>
              </div>
              <div className="flex space-x-3 pt-4">
                <button
                  type="submit"
                  className="btn-primary flex-1"
                  disabled={updateClassMutation.isLoading}
                >
                  {updateClassMutation.isLoading ? 'Updating...' : 'Update Class'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowEditModal(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* User Details Modal */}
      {showUserDetails && selectedUser && (
        <UserDetails
          user={selectedUser}
          bookings={userBookings} // Передаем отфильтрованные бронирования
          onClose={() => {
            setShowUserDetails(false);
            setSelectedUser(null);
            setUserBookings([]); // Очищаем состояние бронирований при закрытии
          }}
          onBookClass={handleBookClassForUser}
          onEditUser={handleEditUser}
          onDeactivateUser={handleDeactivateUser}
        />
      )}
    </div>
  );
}; 