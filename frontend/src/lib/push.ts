import { api } from './api';
import axios from 'axios';

const VAPID_PUBLIC_KEY = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY || 'BJZfDd76XxBDteP3n5ZjPCDz4-SJHeg9N174hPS6m6Q8Iz_bxXSHrduSItz-OHaK2dLglvjkY8GJjoV_EFZcat4';

function urlBase64ToUint8Array(base64String: string) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
        .replace(/\-/g, '+')
        .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

export async function subscribeToPush(): Promise<boolean> {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        console.warn('Push not supported');
        return false;
    }

    try {
        const registration = await navigator.serviceWorker.ready;

        // Check existing
        let subscription = await registration.pushManager.getSubscription();

        if (!subscription) {
            const convertedVapidKey = urlBase64ToUint8Array(VAPID_PUBLIC_KEY);
            subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: convertedVapidKey
            });
        }

        // Send to backend
        // Since api.ts client uses axios instance, we can use it or raw fetch.
        // We need to match backend route structure: { endpoint, keys: { p256dh, auth } }
        const subJson = subscription.toJSON();

        if (!subJson.keys) {
            throw new Error("No keys generated");
        }

        if (!subJson.endpoint) {
            throw new Error("No endpoint generated");
        }

        await api.notifications.subscribe({
            endpoint: subJson.endpoint,
            keys: subJson.keys as { p256dh: string; auth: string }
        });

        console.log('Subscribed to push notifications');
        return true;
    } catch (error) {
        console.error('Failed to subscribe:', error);
        return false;
    }
}

export async function unsubscribeFromPush(): Promise<boolean> {
    if (!('serviceWorker' in navigator)) return false;

    try {
        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.getSubscription();

        if (subscription) {
            await subscription.unsubscribe();
            // Notify backend
            await api.notifications.unsubscribe(subscription.endpoint);
        }
        return true;
    } catch (error) {
        console.error('Failed to unsubscribe:', error);
        return false;
    }
}
