import { useEffect } from 'react';
import { create } from 'zustand';
import { toast } from 'sonner';
import { notificationApi } from '../api/api';
import { useAuthStore } from './useAuthStore';

export const useNotificationStore = create((set, get) => ({
    unreadCount: 0,
    notifications: [],
    isConnected: false,

    setNotifications: (data) => set({ notifications: data }),
    setUnreadCount: (count) => set({ unreadCount: count }),
    addNotification: (notification) => {
        set((state) => ({
            notifications: [notification, ...state.notifications],
            unreadCount: state.unreadCount + 1,
        }));
    },
    fetchNotifications: async (userId) => {
        if (!userId) return;
        try {
            const res = await notificationApi.get(`/notifications/${userId}`);
            const notifications = res.data.notifications || [];
            set({ notifications });
            const unread = notifications.filter(n => !n.read).length;
            set({ unreadCount: unread });
        } catch (error) {
            console.error('Error fetching notifications:', error);
        }
    },
    markRead: async (notificationId) => {
        try {
            await notificationApi.put(`/notifications/${notificationId}/mark-read`);
            set((state) => ({
                notifications: state.notifications.map((n) =>
                    n.id === notificationId ? { ...n, read: true } : n
                ),
                unreadCount: Math.max(0, state.unreadCount - 1)
            }));
        } catch (error) {
            console.error('Error marking read:', error);
        }
    },
    markAllRead: async (userId) => {
        try {
            await notificationApi.put(`/notifications/${userId}/mark-all-read`);
            set((state) => ({
                notifications: state.notifications.map((n) => ({ ...n, read: true })),
                unreadCount: 0
            }));
        } catch (error) {
            console.error('Error marking all read:', error);
        }
    },
    deleteNotification: async (notificationId) => {
        try {
            await notificationApi.delete(`/notifications/${notificationId}`);
            set((state) => {
                const item = state.notifications.find(n => n.id === notificationId);
                return {
                    notifications: state.notifications.filter(n => n.id !== notificationId),
                    unreadCount: item && !item.read ? Math.max(0, state.unreadCount - 1) : state.unreadCount
                }
            });
        } catch (error) {
            console.error('Error deleting notification:', error);
        }
    }
}));

export function useNotificationWebsocket() {
    const { user } = useAuthStore();
    const { addNotification, fetchNotifications } = useNotificationStore();

    useEffect(() => {
        if (!user?.id) return;

        fetchNotifications(user.id);

        let ws = null;
        let reconnectTimer = null;
        let isMounted = true;

        const connect = () => {
            ws = new WebSocket(`ws://localhost:8002/ws/${user.id}`);

            ws.onopen = () => {
                useNotificationStore.setState({ isConnected: true });
                console.log('WS connected');
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    addNotification(data);
                    toast.info(data.message || 'New notification', {
                        description: new Date(data.timestamp || Date.now()).toLocaleTimeString()
                    });
                } catch (e) {
                    console.error("Failed to parse ws message", e);
                }
            };

            ws.onclose = () => {
                if (!isMounted) return;
                useNotificationStore.setState({ isConnected: false });
                console.log('WS disconnected, reconnecting in 5s...');
                reconnectTimer = setTimeout(connect, 5000);
            };

            ws.onerror = (err) => {
                if (!isMounted) return;
                console.error('WS Error');
                ws.close();
            };
        };

        connect();

        return () => {
            isMounted = false;
            clearTimeout(reconnectTimer);
            if (ws) {
                ws.onclose = null; // Prevent reconnect on unmount
                ws.close();
            }
        };
    }, [user?.id]);
}
