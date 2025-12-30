import { db } from '../db';
import { Draft, PendingMessage } from '../db/schema';

import { messagesApi } from '../api';

class SyncManager {
  private isOnline: boolean = typeof navigator !== 'undefined' ? navigator.onLine : true;
  private syncInterval: NodeJS.Timeout | null = null;
  private listeners: ((online: boolean) => void)[] = [];

  constructor() {
    if (typeof window !== 'undefined') {
      window.addEventListener('online', this.handleOnline);
      window.addEventListener('offline', this.handleOffline);
    }
  }

  public subscribe(listener: (online: boolean) => void) {
    this.listeners.push(listener);
    listener(this.isOnline);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private notifyListeners() {
    this.listeners.forEach(listener => listener(this.isOnline));
  }

  private handleOnline = () => {
    this.isOnline = true;
    this.notifyListeners();
    console.log('[SyncManager] Online. Starting sync...');
    this.processQueue();
  };

  private handleOffline = () => {
    this.isOnline = false;
    this.notifyListeners();
    console.log('[SyncManager] Offline. Pausing sync.');
  };

  public get online() {
    return this.isOnline;
  }

  public async addToQueue(content: string, sessionId: string) {
    // Add to IndexedDB
    await db.pendingMessages.add({
      content,
      sessionId,
      createdAt: Date.now(),
      status: 'pending',
      retryCount: 0
    });

    // If we happen to be online (maybe flaky connection or explicit retry), try processing
    if (this.isOnline) {
      this.processQueue();
    }
  }

  public async processQueue() {
    if (!this.isOnline) return;

    const pending = await db.pendingMessages
      .where('status')
      .equals('pending')
      .sortBy('createdAt');

    if (pending.length === 0) return;

    console.log(`[SyncManager] Processing ${pending.length} messages...`);

    for (const msg of pending) {
      try {
        // Mark as sending
        await db.pendingMessages.update(msg.id!, { status: 'sending' });

        // Send using the actual API client
        await messagesApi.send(msg.content, msg.sessionId);

        console.log(`[SyncManager] Sent message ${msg.id}`);

        // Remove from queue on success
        await db.pendingMessages.delete(msg.id!);

      } catch (error) {
        console.error(`[SyncManager] Failed to send message ${msg.id}`, error);
        // Revert to pending, increment retry
        await db.pendingMessages.update(msg.id!, {
          status: 'pending', // or 'failed' if retries > max
          retryCount: (msg.retryCount || 0) + 1
        });
      }
    }
  }
}

export const syncManager = new SyncManager();
