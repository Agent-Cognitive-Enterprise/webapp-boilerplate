export function formatTimestamp(iso: string): string {
    const date = new Date(iso);
    const now = new Date();

    const diffMs = now.getTime() - date.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));

    // Within the last hour -> "# min ago"
    if (diffMinutes >= 0 && diffMinutes < 60) {
        return `${Math.max(1, diffMinutes)} min ago`;
    }

    // Within today (local time) -> local time without date
    const isToday =
        date.getFullYear() === now.getFullYear() &&
        date.getMonth() === now.getMonth() &&
        date.getDate() === now.getDate();

    if (isToday) {
        return date.toLocaleTimeString([], {hour: "numeric", minute: "2-digit"});
    }

    // Otherwise -> full local date-time
    return date.toLocaleString();
}

export function getInitials(fullName: string): string {
    const words = fullName.trim().split(/\s+/);
    return (words[0][0] + words[words.length - 1][0]).toUpperCase();
}

export interface ParsedUrl {
    domain: string;
    path: string;
    fullUrl: string;
}

/**
 * Parse a URL into domain and path components
 */
export function parseUrl(url: string): ParsedUrl | null {
    try {
        const urlObj = new URL(url);
        const domain = urlObj.hostname;
        const path = urlObj.pathname + urlObj.search + urlObj.hash;
        return {
            domain,
            path: path === "/" ? "" : path,
            fullUrl: url,
        };
    } catch {
        return null;
    }
}

/**
 * Get the root domain from a hostname (e.g., "www.example.com" -> "example.com")
 * Note: This is a simple implementation that works for most common cases.
 * For production use with complex TLDs (e.g., co.uk, com.au), consider using a library like psl (Public Suffix List).
 */
export function getRootDomain(hostname: string): string {
    const parts = hostname.split(".");
    // For simple cases, take last two parts (e.g., example.com)
    // This handles: example.com, www.example.com, subdomain.example.com
    if (parts.length >= 2) {
        return parts.slice(-2).join(".");
    }
    return hostname;
}
