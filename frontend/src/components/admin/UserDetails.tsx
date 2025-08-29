import React, { useState } from 'react';
import { User, Calendar, BookOpen, TrendingUp, Plus, X, Clock, Users, Edit, CheckCircle } from 'lucide-react';
import { format } from 'date-fns';
import { enUS } from 'date-fns/locale';

interface UserDetailsProps {
    user: any;
    bookings: any[];
    onClose: () => void;
    onBookClass: (userId: string) => void;
    onEditUser?: (user: any) => void;
    onDeactivateUser?: (userId: string) => void;
}

export const UserDetails: React.FC<UserDetailsProps> = ({
    user,
    bookings,
    onClose,
    onBookClass,
    onEditUser,
    onDeactivateUser
}) => {
    const [activeTab, setActiveTab] = useState<'overview' | 'bookings' | 'statistics'>('overview');

    // Debug logging
    console.log('UserDetails - User data:', user);
    console.log('UserDetails - User ID:', user.id);
    console.log('UserDetails - Bookings data:', bookings);
    console.log('UserDetails - Bookings length:', bookings.length);

    // Debug: check if bookings have user info
    if (bookings.length > 0) {
        console.log('UserDetails - First booking user ID:', bookings[0]?.user?.id);
        console.log('UserDetails - First booking user_id:', bookings[0]?.user_id);
        console.log('UserDetails - User ID match:', bookings[0]?.user?.id === user.id || bookings[0]?.user_id === user.id);
    }

    const tabs = [
        { id: 'overview', label: 'Overview', icon: User },
        { id: 'bookings', label: 'Bookings', icon: BookOpen },
        { id: 'statistics', label: 'Statistics', icon: TrendingUp },
    ];

    // Calculate statistics using status from backend
    const totalBookings = bookings.length;
    const activeBookings = bookings.filter(b => b.status === 'active').length;
    const cancelledBookings = bookings.filter(b => b.status === 'cancelled').length;
    const completedBookings = bookings.filter(b => b.status === 'completed').length;
    const upcomingBookings = bookings.filter(b => new Date(b.date) > new Date()).length;

    const mostBookedClass = bookings.reduce((acc, booking) => {
        const className = booking.class_info?.name || 'Unknown';
        acc[className] = (acc[className] || 0) + 1;
        return acc;
    }, {} as Record<string, number>);

    const favoriteClass = Object.entries(mostBookedClass)
        .sort(([, a], [, b]) => (b as number) - (a as number))[0];

    console.log('UserDetails - Statistics:', {
        totalBookings,
        activeBookings,
        cancelledBookings,
        upcomingBookings,
        favoriteClass
    });

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-gray-200">
                    <div className="flex items-center space-x-3">
                        <User className="h-6 w-6 text-gray-600" />
                        <div>
                            <h2 className="text-xl font-semibold text-gray-900">{user.name}</h2>
                            <p className="text-sm text-gray-600">{user.email}</p>
                        </div>
                    </div>
                    <div className="flex items-center space-x-2">
                        <button
                            onClick={() => onBookClass(user.id)}
                            className="btn-primary flex items-center space-x-2"
                        >
                            <Plus className="h-4 w-4" />
                            <span>Book Class</span>
                        </button>
                        <button
                            onClick={onClose}
                            className="p-2 text-gray-400 hover:text-gray-600"
                        >
                            <X className="h-5 w-5" />
                        </button>
                    </div>
                </div>

                {/* Tabs */}
                <div className="border-b border-gray-200">
                    <nav className="flex space-x-8 px-6">
                        {tabs.map((tab) => {
                            const Icon = tab.icon;
                            return (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id as any)}
                                    className={`flex items-center space-x-2 py-4 border-b-2 font-medium text-sm ${activeTab === tab.id
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

                {/* Content */}
                <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
                    {activeTab === 'overview' && (
                        <div className="space-y-6">
                            {/* User Info */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="card">
                                    <div className="flex items-center justify-between mb-4">
                                        <h3 className="text-lg font-semibold text-gray-900">User Information</h3>
                                        <div className="flex items-center space-x-2">
                                            {onEditUser && (
                                                <button
                                                    onClick={() => onEditUser(user)}
                                                    className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors duration-200"
                                                >
                                                    <Edit className="h-4 w-4 mr-1" />
                                                    Edit
                                                </button>
                                            )}
                                            {onDeactivateUser && (
                                                <button
                                                    onClick={() => onDeactivateUser(user.id)}
                                                    className={`inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md transition-colors duration-200 ${user.is_active
                                                        ? 'text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500'
                                                        : 'text-green-700 bg-green-100 hover:bg-green-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500'
                                                        }`}
                                                >
                                                    {user.is_active ? (
                                                        <>
                                                            <X className="h-4 w-4 mr-1" />
                                                            Deactivate
                                                        </>
                                                    ) : (
                                                        <>
                                                            <User className="h-4 w-4 mr-1" />
                                                            Activate
                                                        </>
                                                    )}
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                    <div className="space-y-3">
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Name:</span>
                                            <span className="font-medium">{user.name}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Email:</span>
                                            <span className="font-medium">{user.email}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Role:</span>
                                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${user.role === 'admin'
                                                ? 'bg-purple-100 text-purple-800'
                                                : 'bg-gray-100 text-gray-800'
                                                }`}>
                                                {user.role}
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Status:</span>
                                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${user.is_active
                                                ? 'bg-green-100 text-green-800'
                                                : 'bg-red-100 text-red-800'
                                                }`}>
                                                {user.is_active ? 'Active' : 'Inactive'}
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Member since:</span>
                                            <span className="font-medium">
                                                {format(new Date(user.created_at), 'd MMM yyyy', { locale: enUS })}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                <div className="card">
                                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Stats</h3>
                                    <div className="space-y-4">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center space-x-2">
                                                <BookOpen className="h-5 w-5 text-blue-600" />
                                                <span className="text-gray-600">Total bookings:</span>
                                            </div>
                                            <span className="text-2xl font-bold text-gray-900">{totalBookings}</span>
                                        </div>
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center space-x-2">
                                                <Calendar className="h-5 w-5 text-green-600" />
                                                <span className="text-gray-600">Upcoming:</span>
                                            </div>
                                            <span className="text-2xl font-bold text-green-600">{upcomingBookings}</span>
                                        </div>
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center space-x-2">
                                                <TrendingUp className="h-5 w-5 text-purple-600" />
                                                <span className="text-gray-600">Favorite class:</span>
                                            </div>
                                            <span className="font-medium text-gray-900">
                                                {favoriteClass ? favoriteClass[0] : 'None'}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Recent Bookings */}
                            <div className="card">
                                <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Bookings</h3>
                                {bookings.slice(0, 5).length > 0 ? (
                                    <div className="space-y-3">
                                        {bookings.slice(0, 5).map((booking) => (
                                            <div key={booking.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                                <div>
                                                    <div className="font-medium text-gray-900">
                                                        {booking.class_info?.name || 'Unknown Class'}
                                                    </div>
                                                    <div className="text-sm text-gray-600">
                                                        {booking.class_info?.teacher} • {format(new Date(booking.date), 'd MMM yyyy', { locale: enUS })}
                                                    </div>
                                                </div>
                                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800`}>
                                                    Confirmed
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-gray-500 text-center py-4">No bookings yet</p>
                                )}
                            </div>
                        </div>
                    )}

                    {activeTab === 'bookings' && (
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg font-semibold text-gray-900">All Bookings</h3>
                                <span className="text-sm text-gray-600">{bookings.length} total</span>
                            </div>

                            {bookings.length > 0 ? (
                                <div className="card">
                                    <div className="overflow-x-auto">
                                        <table className="min-w-full divide-y divide-gray-200">
                                            <thead className="bg-gray-50">
                                                <tr>
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
                                                        Status
                                                    </th>
                                                </tr>
                                            </thead>
                                            <tbody className="bg-white divide-y divide-gray-200">
                                                {bookings.map((booking) => {
                                                    const status = (booking.status || 'active') as 'active' | 'cancelled' | 'completed';
                                                    const statusConfig = {
                                                        active: { text: 'Active', bgColor: 'bg-green-100', textColor: 'text-green-800' },
                                                        cancelled: { text: 'Cancelled', bgColor: 'bg-red-100', textColor: 'text-red-800' },
                                                        completed: { text: 'Completed', bgColor: 'bg-blue-100', textColor: 'text-blue-800' }
                                                    };

                                                    // Safe access to status config
                                                    const currentStatus = statusConfig[status] || statusConfig.active;

                                                    return (
                                                        <tr key={booking.id}>
                                                            <td className="px-6 py-4 whitespace-nowrap">
                                                                <div className="text-sm font-medium text-gray-900">
                                                                    {booking.class_info?.name || 'Unknown'}
                                                                </div>
                                                            </td>
                                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                                {booking.class_info?.teacher || 'Unknown'}
                                                            </td>
                                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                                {format(new Date(booking.date), 'd MMMM yyyy', { locale: enUS })} at{' '}
                                                                {booking.class_info?.start_time ?
                                                                    format(new Date(`2000-01-01T${booking.class_info.start_time}`), 'HH:mm') :
                                                                    'Unknown'
                                                                }
                                                            </td>
                                                            <td className="px-6 py-4 whitespace-nowrap">
                                                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${currentStatus.bgColor} ${currentStatus.textColor}`}>
                                                                    {currentStatus.text}
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
                                        No bookings
                                    </h3>
                                    <p className="text-gray-600">
                                        This user hasn't made any bookings yet
                                    </p>
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === 'statistics' && (
                        <div className="space-y-6">
                            {/* Booking Statistics */}
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                                <div className="card">
                                    <div className="flex items-center">
                                        <div className="p-3 rounded-lg bg-blue-100">
                                            <BookOpen className="h-6 w-6 text-blue-600" />
                                        </div>
                                        <div className="ml-4">
                                            <p className="text-sm font-medium text-gray-600">Total bookings</p>
                                            <p className="text-2xl font-bold text-gray-900">{totalBookings}</p>
                                        </div>
                                    </div>
                                </div>

                                <div className="card">
                                    <div className="flex items-center">
                                        <div className="p-3 rounded-lg bg-green-100">
                                            <Calendar className="h-6 w-6 text-green-600" />
                                        </div>
                                        <div className="ml-4">
                                            <p className="text-sm font-medium text-gray-600">Active</p>
                                            <p className="text-2xl font-bold text-gray-900">{activeBookings}</p>
                                        </div>
                                    </div>
                                </div>

                                <div className="card">
                                    <div className="flex items-center">
                                        <div className="p-3 rounded-lg bg-red-100">
                                            <X className="h-6 w-6 text-red-600" />
                                        </div>
                                        <div className="ml-4">
                                            <p className="text-sm font-medium text-gray-600">Cancelled</p>
                                            <p className="text-2xl font-bold text-gray-900">{cancelledBookings}</p>
                                        </div>
                                    </div>
                                </div>

                                <div className="card">
                                    <div className="flex items-center">
                                        <div className="p-3 rounded-lg bg-purple-100">
                                            <Clock className="h-6 w-6 text-purple-600" />
                                        </div>
                                        <div className="ml-4">
                                            <p className="text-sm font-medium text-gray-600">Upcoming</p>
                                            <p className="text-2xl font-bold text-gray-900">{upcomingBookings}</p>
                                        </div>
                                    </div>
                                </div>

                                <div className="card">
                                    <div className="flex items-center">
                                        <div className="p-3 rounded-lg bg-blue-100">
                                            <CheckCircle className="h-6 w-6 text-blue-600" />
                                        </div>
                                        <div className="ml-4">
                                            <p className="text-sm font-medium text-gray-600">Completed</p>
                                            <p className="text-2xl font-bold text-gray-900">{completedBookings}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Class Preferences */}
                            <div className="card">
                                <h3 className="text-lg font-semibold text-gray-900 mb-4">Class Preferences</h3>
                                {Object.keys(mostBookedClass).length > 0 ? (
                                    <div className="space-y-3">
                                        {Object.entries(mostBookedClass)
                                            .sort(([, a], [, b]) => (b as number) - (a as number))
                                            .slice(0, 5)
                                            .map(([className, count]) => (
                                                <div key={className} className="flex items-center justify-between">
                                                    <span className="text-gray-900">{className}</span>
                                                    <div className="flex items-center space-x-2">
                                                        <div className="w-32 bg-gray-200 rounded-full h-2">
                                                            <div
                                                                className="bg-primary-600 h-2 rounded-full"
                                                                style={{ width: `${((count as number) / totalBookings) * 100}%` }}
                                                            />
                                                        </div>
                                                        <span className="text-sm text-gray-600">{count as number} bookings</span>
                                                    </div>
                                                </div>
                                            ))}
                                    </div>
                                ) : (
                                    <p className="text-gray-500 text-center py-4">No booking data available</p>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}; 