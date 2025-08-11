export interface User {
    id: string;
    email: string;
    name: string;
    is_active: boolean;
    role: 'admin' | 'user';
    created_at: string;
    updated_at: string;
}

export interface DanceClass {
    id: string;
    name: string;
    teacher: string;
    weekday: number;
    start_time: string;
    capacity: number;
    available_spots?: number; // Добавляем поле для доступных мест
    active: boolean;
    created_at: string;
    updated_at: string;
}

export interface Booking {
    id: string;
    user_id: string;
    class_id: string;
    date: string;
    created_at: string;
    class_info?: DanceClass;
    user?: User;
}

export interface ScheduleStatistics {
    total_classes: number;
    active_classes: number;
    total_teachers: number;
    classes_by_weekday: Array<{ weekday: number; count: number }>;
}

export interface BookingStatistics {
    total_bookings: number;
    bookings_today: number;
    bookings_this_week: number;
    most_popular_class?: string;
}

export interface AdminStatistics {
    bookings_today: number;
    active_users: number;
    revenue_month: number;
    total_bookings: number;
    bookings_this_week: number;
    most_popular_class?: {
        id: string;
        name: string;
    };
}

export interface LoginCredentials {
    username: string;
    password: string;
}

export interface RegisterData {
    email: string;
    name: string;
    password: string;
}

export interface UserUpdateData {
    name: string;
}

export interface PasswordChangeData {
    current_password: string;
    new_password: string;
}

export interface UserUpdateAdminData {
    role: 'admin' | 'user';
    is_active: boolean;
}

export interface BookingRequest {
    class_id: string;
    date: string;
}

export interface AdminBookingRequest {
    user_id: string;
    class_id: string;
    date: string;
}

export interface ApiResponse<T> {
    data: T;
    message?: string;
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    size: number;
    pages: number;
}

export type Weekday = 0 | 1 | 2 | 3 | 4 | 5 | 6;

export const WEEKDAYS = {
    0: 'Sunday',
    1: 'Monday',
    2: 'Tuesday',
    3: 'Wednesday',
    4: 'Thursday',
    5: 'Friday',
    6: 'Saturday',
} as const; 