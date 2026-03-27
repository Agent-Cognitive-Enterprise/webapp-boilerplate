import {defineConfig, loadEnv} from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

const HSTS_HEADER_VALUE = "max-age=31536000; includeSubDomains";

function resolveApiOrigin(apiUrl: string): string | null {
    const match = apiUrl.match(/^[a-zA-Z][a-zA-Z\d+.-]*:\/\/[^/]+/);
    return match ? match[0] : null;
}

function buildCspHeader(
    apiOrigin: string | null,
    includeDevScriptEscapes: boolean,
    includeDevSockets: boolean,
): string {
    const connectSources = ["'self'"];
    if (apiOrigin) {
        connectSources.push(apiOrigin);
    }
    if (includeDevSockets) {
        connectSources.push("ws:", "wss:");
    }

    const scriptSources = ["'self'"];
    if (includeDevScriptEscapes) {
        scriptSources.push("'unsafe-inline'", "'unsafe-eval'");
    }

    return [
        "default-src 'self'",
        "base-uri 'self'",
        "frame-ancestors 'none'",
        "object-src 'none'",
        "form-action 'self'",
        `script-src ${scriptSources.join(" ")}`,
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "img-src 'self' data: blob:",
        "font-src 'self' data: https://fonts.gstatic.com",
        `connect-src ${connectSources.join(" ")}`,
    ].join("; ");
}

function buildSecurityHeaders(
    apiOrigin: string | null,
    includeDevScriptEscapes: boolean,
    includeDevSockets: boolean,
): Record<string, string> {
    return {
        "Strict-Transport-Security": HSTS_HEADER_VALUE,
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": buildCspHeader(
            apiOrigin,
            includeDevScriptEscapes,
            includeDevSockets,
        ),
    };
}

// https://vite.dev/config/
export default defineConfig(({mode}) => {
    const env = loadEnv(mode, ".", "");
    const apiOrigin = resolveApiOrigin(env.VITE_API_URL || "http://localhost:8000");

    return {
        plugins: [
            react(),
            tailwindcss(),
        ],
        server: {
            host: "0.0.0.0",
            port: 5173,
            headers: buildSecurityHeaders(apiOrigin, true, true),
        },
        preview: {
            headers: buildSecurityHeaders(apiOrigin, false, false),
        },
    };
});
