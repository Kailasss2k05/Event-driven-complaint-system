import { useEffect } from 'react';
import { useAuthStore } from '../hooks/useAuthStore';
import { useNotificationStore } from '../hooks/useNotifications';
import { format } from 'date-fns';
import { Bell, Check, Trash2, CheckCircle2 } from 'lucide-react';
import { cn } from '../utils/cn';

export const Notifications = () => {
    const { user } = useAuthStore();
    const {
        notifications,
        fetchNotifications,
        markRead,
        markAllRead,
        deleteNotification
    } = useNotificationStore();

    useEffect(() => {
        if (user?.id) {
            fetchNotifications(user.id);
        }
    }, [user?.id, fetchNotifications]);

    const unread = (notifications || []).filter(n => !n.read).length;

    return (
        <div className="max-w-4xl mx-auto py-8">
            <div className="flex justify-between items-end mb-8 border-b border-gray-200 pb-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                        <Bell className="w-8 h-8 text-primary-600" /> Notifications
                    </h1>
                    <p className="text-gray-500 mt-2">
                        You have {unread} unread message{unread !== 1 ? 's' : ''}
                    </p>
                </div>

                {notifications.length > 0 && unread > 0 && (
                    <button
                        onClick={() => markAllRead(user.id)}
                        className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                        <CheckCircle2 className="w-4 h-4 text-green-500" />
                        Mark all as read
                    </button>
                )}
            </div>

            {notifications.length === 0 ? (
                <div className="text-center py-20 bg-white rounded-2xl border border-dashed border-gray-300">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-50 mb-4">
                        <Bell className="w-8 h-8 text-gray-400" />
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 mb-1">All caught up!</h3>
                    <p className="text-gray-500">You don't have any notifications right now.</p>
                </div>
            ) : (
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden divide-y divide-gray-100">
                    {notifications.map((notification) => (
                        <div
                            key={notification.id}
                            className={cn(
                                "p-4 sm:p-6 transition-colors group flex items-start gap-4 hover:bg-gray-50",
                                !notification.read ? "bg-blue-50/50" : "bg-white"
                            )}
                        >
                            <div className="mt-1">
                                {notification.notification_type === 'STATUS_UPDATE' ? (
                                    <div className="w-10 h-10 rounded-full bg-orange-100 flex flex-shrink-0 items-center justify-center text-orange-600">
                                        <CheckCircle2 className="w-5 h-5" />
                                    </div>
                                ) : notification.notification_type === 'SYSTEM' ? (
                                    <div className="w-10 h-10 rounded-full bg-purple-100 flex flex-shrink-0 items-center justify-center text-purple-600">
                                        <Bell className="w-5 h-5" />
                                    </div>
                                ) : (
                                    <div className="w-10 h-10 rounded-full bg-blue-100 flex flex-shrink-0 items-center justify-center text-blue-600">
                                        <Bell className="w-5 h-5" />
                                    </div>
                                )}
                            </div>

                            <div className="flex-1 min-w-0">
                                <div className="flex justify-between items-start mb-1">
                                    <h4 className={cn(
                                        "text-sm font-medium",
                                        !notification.read ? "text-gray-900 font-bold" : "text-gray-800"
                                    )}>
                                        {notification.title || 'Notification'}
                                    </h4>
                                    <span className="text-xs text-gray-500 whitespace-nowrap ml-4">
                                        {format(new Date(notification.timestamp || Date.now()), 'MMM d, h:mm a')}
                                    </span>
                                </div>
                                <p className={cn(
                                    "text-sm",
                                    !notification.read ? "text-gray-700 font-medium" : "text-gray-500"
                                )}>
                                    {notification.message}
                                </p>
                            </div>

                            <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                {!notification.read && (
                                    <button
                                        onClick={() => markRead(notification.id)}
                                        className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-full transition-colors"
                                        title="Mark as read"
                                    >
                                        <Check className="w-4 h-4" />
                                    </button>
                                )}
                                <button
                                    onClick={() => deleteNotification(notification.id)}
                                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-full transition-colors"
                                    title="Delete"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};
