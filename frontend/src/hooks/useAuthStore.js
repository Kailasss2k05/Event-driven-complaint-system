import { create } from 'zustand';
import { api } from '../api/api';

export const useAuthStore = create((set, get) => ({
    user: null, // { role: 'user' | 'department_admin' | 'super_admin', id, ... }
    token: localStorage.getItem('token') || null,
    isAuthenticated: !!localStorage.getItem('token'),
    isLoading: false,

    login: async (username, password) => {
        set({ isLoading: true });
        try {
            const data = new URLSearchParams({ username, password });
            const res = await api.post('/auth/token', data, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            });
            const token = res.data.access_token;

            localStorage.setItem('token', token);

            // Fetch user info
            const meRes = await api.get('/auth/me', {
                headers: { Authorization: `Bearer ${token}` }
            });

            set({
                user: meRes.data,
                token,
                isAuthenticated: true,
                isLoading: false
            });
            return meRes.data.role;
        } catch (error) {
            set({ isLoading: false });
            throw error;
        }
    },

    fetchUser: async () => {
        const token = get().token;
        if (!token) return;

        set({ isLoading: true });
        try {
            const meRes = await api.get('/auth/me');
            set({ user: meRes.data, isAuthenticated: true, isLoading: false });
        } catch (error) {
            // Token invalid or expired
            get().logout();
            set({ isLoading: false });
        }
    },

    logout: () => {
        localStorage.removeItem('token');
        set({ user: null, token: null, isAuthenticated: false });
        // Redirect should happen in the UI layer
    }
}));
