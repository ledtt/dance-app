import React, { createContext, useContext, useEffect, useState } from 'react';
import { User } from '@/types';
import { apiClient } from '@/api/client';
import toast from 'react-hot-toast';

interface AuthContextType {
    user: User | null;
    isLoading: boolean;
    login: (email: string, password: string) => Promise<void>;
    register: (email: string, name: string, password: string) => Promise<void>;
    logout: () => void;
    refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

interface AuthProviderProps {
    children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            apiClient.getCurrentUser()
                .then((userData) => {
                    setUser(userData);
                })
                .catch(() => {
                    localStorage.removeItem('token');
                    localStorage.removeItem('user');
                })
                .finally(() => {
                    setIsLoading(false);
                });
        } else {
            setIsLoading(false);
        }
    }, []);

    const login = async (email: string, password: string) => {
        try {
            const response = await apiClient.login({ username: email, password });
            localStorage.setItem('token', response.access_token);

            const userData = await apiClient.getCurrentUser();
            setUser(userData);
            localStorage.setItem('user', JSON.stringify(userData));

            toast.success('Login successful!');
        } catch (error) {
            console.error('Login error:', error);
            toast.error('Login error. Please check your email and password.');
        }
    };

    const register = async (email: string, name: string, password: string) => {
        try {
            await apiClient.register({ email, name, password });
            toast.success('Registration successful! You can now log in.');
        } catch (error) {
            console.error('Registration error:', error);
            toast.error('Registration error. Please try again.');
        }
    };

    const logout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setUser(null);
        toast.success('You have logged out of the system');
    };

    const refreshUser = async () => {
        try {
            const userData = await apiClient.getCurrentUser();
            setUser(userData);
            localStorage.setItem('user', JSON.stringify(userData));
        } catch (error) {
            console.error('Failed to refresh user data:', error);
            // If refresh fails, user might be logged out
            logout();
        }
    };

    const value: AuthContextType = {
        user,
        isLoading,
        login,
        register,
        logout,
        refreshUser,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}; 