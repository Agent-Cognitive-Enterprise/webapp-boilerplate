export type SessionInvalidationReason = "refresh_failed";

type SessionInvalidationListener = (reason: SessionInvalidationReason) => void;

const listeners = new Set<SessionInvalidationListener>();

export function subscribeToSessionInvalidation(listener: SessionInvalidationListener): () => void {
    listeners.add(listener);
    return () => {
        listeners.delete(listener);
    };
}

export function notifySessionInvalidated(reason: SessionInvalidationReason): void {
    listeners.forEach((listener) => {
        listener(reason);
    });
}
