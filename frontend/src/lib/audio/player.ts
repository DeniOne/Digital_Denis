/**
 * Digital Denis — Audio Player Utility
 */

export class StreamAudioPlayer {
    private audio: HTMLAudioElement | null = null;

    play(url: string, onEnded?: () => void): void {
        this.stop();

        this.audio = new Audio(url);
        this.audio.play().catch(err => {
            console.error('Playback failed:', err);
        });

        if (onEnded) {
            this.audio.onended = onEnded;
        }
    }

    stop(): void {
        if (this.audio) {
            this.audio.pause();
            this.audio.currentTime = 0;
            this.audio = null;
        }
    }

    setVolume(volume: number): void {
        if (this.audio) {
            this.audio.volume = Math.max(0, Math.min(1, volume));
        }
    }
}

export const streamPlayer = new StreamAudioPlayer();
