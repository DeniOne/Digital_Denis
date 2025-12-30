export interface Draft {
    id?: number;
    content: string;
    createdAt: number;
}

export interface PendingMessage {
    id?: number;
    content: string;
    sessionId: string;
    createdAt: number;
    status: 'pending' | 'sending' | 'failed';
    retryCount: number;
}
