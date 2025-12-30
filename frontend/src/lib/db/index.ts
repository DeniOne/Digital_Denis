import Dexie, { Table } from 'dexie';
import { Draft, PendingMessage } from './schema';

export class AppDB extends Dexie {
    drafts!: Table<Draft>;
    pendingMessages!: Table<PendingMessage>;

    constructor() {
        super('DigitalDenisDB');

        this.version(1).stores({
            drafts: '++id, content, createdAt',
            pendingMessages: '++id, sessionId, status, createdAt' // Indexed fields
        });
    }
}

export const db = new AppDB();
