import axios, { AxiosInstance } from 'axios';
import toast from 'react-hot-toast';
import {
    User,
    DanceClass,
    Booking,
    PaginatedResponse,
    ScheduleStatistics,
    BookingStatistics,
    AdminStatistics,
    UserUpdateData,
    PasswordChangeData,
    UserUpdateAdminData,
    AdminBookingRequest
} from '../types';

class ApiClient {
    private client: AxiosInstance;

    constructor() {
        this.client = axios.create({
            baseURL: '/api',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        // Request interceptor to add auth token
        this.client.interceptors.request.use(
            (config: any) => {
                const token = localStorage.getItem('token');
                if (token) {
                    config.headers.Authorization = `Bearer ${token}`;
                }
                return config;
            },
            (error: any) => {
                return Promise.reject(error);
            }
        );

        // Response interceptor for error handling
        this.client.interceptors.response.use(
            (response: any) => response,
            (error: any) => {
                if (error.response?.status === 401) {
                    // Immediately clear expired/invalid token before redirecting
                    localStorage.removeItem('token');
                    localStorage.removeItem('user');

                    // Show user-friendly message about session expiration
                    toast.error('Your session has expired. Please log in again.');

                    // Redirect to auth page
                    window.location.href = '/auth';
                    return Promise.reject(error);
                }

                if (error.response?.status !== 401) {
                    const message = error.response?.data?.detail || error.message || 'An error occurred';
                    toast.error(message);
                }

                return Promise.reject(error);
            }
        );
    }

    // Auth API
    async login(credentials: { username: string; password: string }): Promise<{ access_token: string; token_type: string }> {
        const formData = new FormData();
        formData.append('username', credentials.username);
        formData.append('password', credentials.password);

        const response = await this.client.post('/auth/login', formData, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        });
        return response.data;
    }

    async register(userData: { email: string; name: string; password: string }): Promise<User> {
        const response = await this.client.post('/auth/register', userData);
        return response.data;
    }

    async getCurrentUser(): Promise<User> {
        const response = await this.client.get('/auth/me');
        return response.data;
    }

    async updateCurrentUser(userData: UserUpdateData): Promise<User> {
        const response = await this.client.put('/auth/me', userData);
        return response.data;
    }

    async changePassword(passwordData: PasswordChangeData): Promise<void> {
        await this.client.post('/auth/me/change-password', passwordData);
    }

    async getAllUsers(params?: {
        page?: number;
        size?: number;
        email?: string;
        name?: string;
    }): Promise<PaginatedResponse<User>> {
        const apiParams = {
            page: params?.page || 1,
            size: params?.size || 50,
            email: params?.email,
            name: params?.name,
        };

        const response = await this.client.get('/auth/admin/users', { params: apiParams });

        // Теперь API возвращает унифицированную структуру PaginatedResponse
        if (response.data && typeof response.data === 'object' && 'items' in response.data) {
            return response.data;
        }

        // Fallback для обратной совместимости
        if (Array.isArray(response.data)) {
            return {
                items: response.data,
                total: response.data.length,
                page: 1,
                size: response.data.length,
                pages: 1,
            };
        }

        return {
            items: [],
            total: 0,
            page: 1,
            size: 0,
            pages: 1,
        };
    }

    async getUserById(userId: string): Promise<User> {
        const response = await this.client.get(`/auth/admin/users/${userId}`);
        return response.data;
    }

    async updateUserByAdmin(userId: string, userData: UserUpdateAdminData): Promise<User> {
        const response = await this.client.put(`/auth/admin/users/${userId}`, userData);
        return response.data;
    }

    async updateUserRole(userId: string, role: 'user' | 'admin'): Promise<User> {
        const response = await this.client.put(`/auth/admin/users/${userId}/role`, { role });
        return response.data;
    }

    // Schedule API
    async getSchedule(params?: {
        teacher?: string;
        weekday?: number;
        name?: string;
        is_active?: boolean;
        page?: number;
        size?: number;
    }): Promise<PaginatedResponse<DanceClass>> {
        // Преобразуем параметры для соответствия backend API
        const apiParams = {
            teacher: params?.teacher,
            weekday: params?.weekday, // Backend теперь ожидает 'weekday'
            name: params?.name,
            active: params?.is_active, // Backend ожидает 'active', а не 'is_active'
            page: params?.page || 1,
            size: params?.size || 100,
        };

        const response = await this.client.get('/schedule/schedule', { params: apiParams });

        // Добавляем отладочные логи
        console.log('API Request params:', apiParams);
        console.log('API Response:', {
            status: response.status,
            data: response.data,
            dataType: typeof response.data,
            isArray: Array.isArray(response.data)
        });

        // Теперь API возвращает унифицированную структуру PaginatedResponse
        if (response.data && typeof response.data === 'object' && 'items' in response.data) {
            console.log('API returned paginated response, items count:', response.data.items.length);
            return response.data;
        }

        // Fallback для обратной совместимости
        if (Array.isArray(response.data)) {
            console.log('API returned array directly (fallback), length:', response.data.length);
            return {
                items: response.data,
                total: response.data.length,
                page: 1,
                size: response.data.length,
                pages: 1,
            };
        }

        // Если API возвращает что-то неожиданное
        console.error('Unexpected API response format:', response.data);
        return {
            items: [],
            total: 0,
            page: 1,
            size: 0,
            pages: 1,
        };
    }

    async getClassById(id: string): Promise<DanceClass> {
        const response = await this.client.get(`/schedule/schedule/${id}`);
        return response.data;
    }

    async createClass(classData: Omit<DanceClass, 'id' | 'created_at' | 'updated_at'>): Promise<DanceClass> {
        const response = await this.client.post('/schedule/schedule', classData);
        return response.data;
    }

    async updateClass(id: string, classData: Partial<DanceClass>): Promise<DanceClass> {
        const response = await this.client.put(`/schedule/schedule/${id}`, classData);
        return response.data;
    }

    async deleteClass(id: string): Promise<void> {
        await this.client.delete(`/schedule/schedule/${id}`);
    }

    async getClassesByTeacher(teacher: string): Promise<DanceClass[]> {
        const response = await this.client.get(`/schedule/schedule/teacher/${teacher}`);
        return response.data;
    }

    async getClassesByWeekday(weekday: number): Promise<DanceClass[]> {
        const response = await this.client.get(`/schedule/schedule/weekday/${weekday}`);
        return response.data;
    }

    async getScheduleStatistics(): Promise<ScheduleStatistics> {
        const response = await this.client.get('/schedule/schedule/statistics');
        return response.data;
    }

    // Booking API
    async createBooking(bookingData: { class_id: string; date: string }): Promise<Booking> {
        const response = await this.client.post('/booking/book', bookingData);
        return response.data;
    }

    async getMyBookings(): Promise<Booking[]> {
        const response = await this.client.get('/booking/my-bookings');
        return response.data;
    }

    async cancelBooking(id: string): Promise<void> {
        await this.client.delete(`/booking/bookings/${id}`);
    }

    async getBookingById(id: string): Promise<Booking> {
        const response = await this.client.get(`/booking/bookings/${id}`);
        return response.data;
    }

    async getAllBookings(params?: {
        date_from?: string;
        date_to?: string;
        user_id?: string;
        teacher?: string;
        class_name?: string;
        page?: number;
        size?: number;
    }): Promise<PaginatedResponse<Booking>> {
        // Преобразуем параметры для соответствия backend API
        const apiParams = {
            date_from: params?.date_from,
            date_to: params?.date_to,
            user_id: params?.user_id,
            teacher: params?.teacher,
            class_name: params?.class_name,
            page: params?.page || 1,
            size: params?.size || 100,
        };

        console.log('getAllBookings - Request params:', apiParams);

        const response = await this.client.get('/booking/admin/bookings', { params: apiParams });

        // Debug logging
        console.log('getAllBookings - API Response:', response.data);
        console.log('getAllBookings - Response type:', typeof response.data);
        console.log('getAllBookings - Is array:', Array.isArray(response.data));

        // Теперь API возвращает унифицированную структуру PaginatedResponse
        if (response.data && typeof response.data === 'object' && 'items' in response.data) {
            console.log('getAllBookings - API returned paginated response, items count:', response.data.items.length);
            return response.data;
        }

        // Fallback для обратной совместимости
        if (Array.isArray(response.data)) {
            console.log('getAllBookings - API returned array directly (fallback), length:', response.data.length);
            // Сортируем по дате (новые сначала)
            const sortedBookings = response.data.sort((a: any, b: any) => {
                const dateA = new Date(a.date);
                const dateB = new Date(b.date);
                return dateB.getTime() - dateA.getTime();
            });

            return {
                items: sortedBookings,
                total: sortedBookings.length,
                page: 1,
                size: sortedBookings.length,
                pages: 1,
            };
        }

        // Если API возвращает что-то неожиданное
        return {
            items: [],
            total: 0,
            page: 1,
            size: 0,
            pages: 1,
        };
    }

    async getBookingStatistics(): Promise<AdminStatistics> {
        const response = await this.client.get('/booking/admin/statistics');
        return response.data;
    }

    async getUserBookings(userId: string): Promise<Booking[]> {
        const response = await this.client.get('/booking/admin/bookings', {
            params: { user_id: userId }
        });
        return response.data;
    }

    async createBookingByAdmin(bookingData: AdminBookingRequest): Promise<Booking> {
        const response = await this.client.post('/booking/admin/bookings', bookingData);
        return response.data;
    }
}

export const apiClient = new ApiClient(); 