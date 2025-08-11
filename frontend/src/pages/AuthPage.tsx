import React, { useState } from 'react';
import { LoginForm } from '@/components/auth/LoginForm';
import { RegisterForm } from '@/components/auth/RegisterForm';
import { Music, Users, Clock } from 'lucide-react';

export const AuthPage: React.FC = () => {
    const [isLogin, setIsLogin] = useState(true);

    return (
        <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-secondary-50 flex">
            {/* Left side - Features */}
            <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary-600 to-primary-700 text-white p-12">
                <div className="max-w-md mx-auto">
                    <div className="mb-8">
                        <h1 className="text-4xl font-bold mb-4">Dance Studio</h1>
                        <p className="text-xl text-primary-100">
                            Book dance classes online
                        </p>
                    </div>

                    <div className="space-y-8">
                        <div className="flex items-start space-x-4">
                            <div className="flex-shrink-0">
                                <Music className="h-8 w-8 text-primary-200" />
                            </div>
                            <div>
                                <h3 className="text-lg font-semibold mb-2">Various Styles</h3>
                                <p className="text-primary-100">
                                    Hip-hop, Contemporary, Ballet, Latin and many other styles
                                </p>
                            </div>
                        </div>

                        <div className="flex items-start space-x-4">
                            <div className="flex-shrink-0">
                                <Users className="h-8 w-8 text-primary-200" />
                            </div>
                            <div>
                                <h3 className="text-lg font-semibold mb-2">Experienced Teachers</h3>
                                <p className="text-primary-100">
                                    Professional dancers with years of teaching experience
                                </p>
                            </div>
                        </div>

                        <div className="flex items-start space-x-4">
                            <div className="flex-shrink-0">
                                <Clock className="h-8 w-8 text-primary-200" />
                            </div>
                            <div>
                                <h3 className="text-lg font-semibold mb-2">Convenient Schedule</h3>
                                <p className="text-primary-100">
                                    Classes at convenient times, flexible schedule for all ages
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="mt-12 pt-8 border-t border-primary-500">
                        <p className="text-primary-200 text-sm">
                            Join our dance community and start your journey in the world of dance!
                        </p>
                    </div>
                </div>
            </div>

            {/* Right side - Auth forms */}
            <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
                <div className="w-full max-w-md">
                    {isLogin ? (
                        <LoginForm onSwitchToRegister={() => setIsLogin(false)} />
                    ) : (
                        <RegisterForm onSwitchToLogin={() => setIsLogin(true)} />
                    )}
                </div>
            </div>
        </div>
    );
}; 