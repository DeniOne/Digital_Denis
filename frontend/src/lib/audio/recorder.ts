/**
 * Digital Den — Audio Recorder Utility
 */

export interface RecorderOptions {
    mimeType?: string;
    audioBitsPerSecond?: number;
    onDataAvailable?: (blob: Blob) => void;
}

export class AudioRecorder {
    private stream: MediaStream | null = null;
    private recorder: MediaRecorder | null = null;

    async start(options: RecorderOptions = {}): Promise<void> {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 16000,
                },
            });

            this.recorder = new MediaRecorder(this.stream, {
                mimeType: options.mimeType || 'audio/webm;codecs=opus',
                audioBitsPerSecond: options.audioBitsPerSecond || 16000,
            });

            this.recorder.ondataavailable = (event) => {
                if (event.data.size > 0 && options.onDataAvailable) {
                    options.onDataAvailable(event.data);
                }
            };

            // Start recording with 500ms intervals
            this.recorder.start(500);
        } catch (error) {
            console.error('Failed to start recording:', error);
            throw error;
        }
    }

    stop(): void {
        if (this.recorder && this.recorder.state !== 'inactive') {
            this.recorder.stop();
        }
        if (this.stream) {
            this.stream.getTracks().forEach((track) => track.stop());
        }
        this.recorder = null;
        this.stream = null;
    }

    get state(): 'inactive' | 'recording' | 'paused' {
        return this.recorder?.state || 'inactive';
    }
}
