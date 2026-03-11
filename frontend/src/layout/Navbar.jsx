import { Outlet, Navigate, Link } from 'react-router-dom';
import { Bell, LogOut, Menu, UserCircle } from 'lucide-react';
import { useAuthStore } from '../hooks/useAuthStore';
import { useNotificationStore } from '../hooks/useNotifications';
import { cn } from '../utils/cn';

const NavLink = ({ to, children, current }) => (
    <Link
        to={to}
        className={cn(
            "px-3 py-2 rounded-md text-sm font-medium transition-colors",
            current
                ? "bg-primary-50 text-primary-700"
                : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
        )}
    >
        {children}
    </Link>
);

export const Navbar = () => {
    const { user, logout } = useAuthStore();
    const { unreadCount } = useNotificationStore();

    const getDashboardLink = () => {
        switch (user?.role) {
            case 'user': return '/submit';
            case 'department_admin': return '/staff';
            case 'super_admin': return '/admin';
            default: return '/';
        }
    };

    return (
        <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16">
                    <div className="flex">
                        <div className="flex-shrink-0 flex items-center">
                            <Link to={getDashboardLink()} className="text-xl font-bold text-primary-600 tracking-tight">
                                CivicResolve
                            </Link>
                        </div>
                        {user?.role === 'user' && (
                            <div className="hidden sm:ml-6 sm:flex sm:space-x-4 items-center">
                                <NavLink to="/submit">Submit</NavLink>
                                <NavLink to="/my-complaints">My Complaints</NavLink>
                            </div>
                        )}
                    </div>

                    <div className="flex items-center space-x-4">
                        <Link
                            to="/notifications"
                            className="p-2 text-gray-500 hover:text-gray-700 rounded-full hover:bg-gray-100 relative transition-colors"
                        >
                            <Bell className="h-5 w-5" />
                            {unreadCount > 0 && (
                                <span className="absolute top-1 right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white ring-2 ring-white">
                                    {unreadCount > 9 ? '9+' : unreadCount}
                                </span>
                            )}
                        </Link>

                        <div className="flex items-center gap-3 pl-4 border-l border-gray-200">
                            <div className="hidden sm:flex flex-col items-end">
                                <span className="text-sm font-medium text-gray-900 leading-tight">
                                    {user?.username || 'User'}
                                </span>
                                <span className="text-xs text-gray-500 capitalize">
                                    {user?.role?.replace('_', ' ')}
                                </span>
                            </div>

                            <button
                                onClick={() => {
                                    logout();
                                    window.location.href = '/login';
                                }}
                                className="p-2 text-gray-500 hover:text-red-600 rounded-full hover:bg-red-50 transition-colors"
                                title="Logout"
                            >
                                <LogOut className="h-5 w-5" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </nav>
    );
};
