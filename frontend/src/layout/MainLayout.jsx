import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';
import { useNotificationWebsocket } from '../hooks/useNotifications';

export const MainLayout = () => {
    // Initialize websocket for notifications
    useNotificationWebsocket();

    return (
        <div className="min-h-screen bg-gray-50 font-sans text-gray-900">
            <Navbar />
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <Outlet />
            </main>
        </div>
    );
};
