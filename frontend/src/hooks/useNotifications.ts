import { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../context/useAuth';

export type InAppNotification = {
  id: number;
  event_type: string;
  title: string;
  message: string;
  target_url: string | null;
  is_read: boolean;
  created_at: string;
};

export const useNotifications = () => {
  const { authFetch } = useAuth();
  const [notifications, setNotifications] = useState<InAppNotification[]>([]);
  const [notificationError, setNotificationError] = useState('');
  const unreadCount = notifications.filter((item) => !item.is_read).length;

  const refreshNotifications = useCallback(async () => {
    try {
      const response = await authFetch('/api/notifications', { cache: 'no-store' });
      if (!response.ok) throw new Error('Notifications could not be loaded.');
      const data = await response.json();
      setNotifications(Array.isArray(data) ? data : []);
      setNotificationError('');
    } catch (error) {
      setNotificationError(error instanceof Error ? error.message : 'Notifications could not be loaded.');
    }
  }, [authFetch]);

  useEffect(() => {
    void refreshNotifications();
    const interval = window.setInterval(() => { void refreshNotifications(); }, 30000);
    return () => window.clearInterval(interval);
  }, [refreshNotifications]);

  const markRead = useCallback(async (id: number) => {
    const response = await authFetch(`/api/notifications/${id}/read`, { method: 'PATCH' });
    if (!response.ok) return false;
    setNotifications((current) => current.map((item) => item.id === id ? { ...item, is_read: true } : item));
    return true;
  }, [authFetch]);

  const markAllRead = useCallback(async () => {
    const response = await authFetch('/api/notifications/read-all', { method: 'POST' });
    if (!response.ok) return false;
    setNotifications((current) => current.map((item) => ({ ...item, is_read: true })));
    return true;
  }, [authFetch]);

  return { notifications, unreadCount, notificationError, refreshNotifications, markRead, markAllRead };
};
