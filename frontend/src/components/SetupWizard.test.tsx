import {describe, it, expect, vi, beforeEach} from "vitest";
import {fireEvent, render, screen, waitFor} from "@testing-library/react";
import {MemoryRouter} from "react-router-dom";
import SetupWizard from "./SetupWizard";
import {runSetup} from "../api/setup";

vi.mock("../api/setup", () => ({
    runSetup: vi.fn(),
}));

function renderWizard(
    isInitialized = false,
    onSetupComplete = vi.fn(),
    emailDefaults: {
        smtp_host?: string | null;
        smtp_port?: number | null;
        smtp_username?: string | null;
        smtp_password?: string | null;
        smtp_from_email?: string | null;
        smtp_use_tls?: boolean;
        auth_frontend_base_url?: string | null;
        auth_backend_base_url?: string | null;
    } | null = null,
) {
    return render(
        <MemoryRouter>
            <SetupWizard
                isInitialized={isInitialized}
                onSetupComplete={onSetupComplete}
                seedLocales={["en", "fr"]}
                emailDefaults={emailDefaults}
            />
        </MemoryRouter>,
    );
}

describe("SetupWizard", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        Object.defineProperty(window.navigator, "language", {
            configurable: true,
            value: "en-US",
        });
    });

    it("renders required fields in uninitialized mode", () => {
        renderWizard();

        expect(screen.getByText("First-Run Setup")).toBeInTheDocument();
        expect(screen.getByText("Initial setup token")).toBeInTheDocument();
        expect(screen.getByText("Site name")).toBeInTheDocument();
        expect(screen.getByText("Supported locales")).toBeInTheDocument();
        expect(screen.getByText("Admin email")).toBeInTheDocument();
        expect(screen.getByText("Admin password")).toBeInTheDocument();
    });

    it("shows validation errors for invalid input", async () => {
        renderWizard();

        fireEvent.click(screen.getByRole("button", {name: /initial/i}));

        await waitFor(() => expect(screen.getByText("Setup token is required.")).toBeInTheDocument());
        expect(screen.getByText("Site name is required.")).toBeInTheDocument();
        expect(screen.getByText("Admin email is required.")).toBeInTheDocument();
        expect(screen.getByText("Admin password is required.")).toBeInTheDocument();
        expect(runSetup).not.toHaveBeenCalled();
    });

    it("submits successfully with valid payload", async () => {
        const onSetupComplete = vi.fn();
        vi.mocked(runSetup).mockResolvedValue({data: {}} as any);

        renderWizard(false, onSetupComplete);

        fireEvent.change(screen.getByLabelText("Initial setup token"), {target: {value: "token-123"}});
        fireEvent.change(screen.getByLabelText("Site name"), {target: {value: "My Site"}});
        fireEvent.change(screen.getByLabelText("Admin email"), {target: {value: "admin@example.com"}});
        fireEvent.change(screen.getByLabelText("Admin password"), {target: {value: "StrongPass123!"}});

        fireEvent.click(screen.getByRole("button", {name: /initial/i}));

        await waitFor(() => expect(runSetup).toHaveBeenCalledTimes(1));
        expect(runSetup).toHaveBeenCalledWith({
            setup_token: "token-123",
            site_name: "My Site",
            default_locale: "en",
            supported_locales: ["en", "fr"],
            admin_email: "admin@example.com",
            admin_password: "StrongPass123!",
        });
        expect(onSetupComplete).toHaveBeenCalledTimes(1);
    });

    it("uses browser locale when supported", () => {
        Object.defineProperty(window.navigator, "language", {
            configurable: true,
            value: "fr-FR",
        });

        renderWizard();

        expect(screen.getByText("Configuration initiale")).toBeInTheDocument();
    });

    it("prefills optional email settings from setup defaults", () => {
        renderWizard(false, vi.fn(), {
            smtp_host: "smtp.env.example.com",
            smtp_port: 587,
            smtp_username: "smtp-user",
            smtp_password: "smtp-pass",
            smtp_from_email: "noreply@example.com",
            smtp_use_tls: true,
            auth_frontend_base_url: "https://app.env.example.com",
            auth_backend_base_url: "https://api.env.example.com",
        });

        expect(screen.getByLabelText("SMTP host")).toHaveValue("smtp.env.example.com");
        expect(screen.getByLabelText("SMTP port")).toHaveValue(587);
        expect(screen.getByLabelText("SMTP username")).toHaveValue("smtp-user");
        expect(screen.getByLabelText("SMTP password")).toHaveValue("smtp-pass");
        expect(screen.getByLabelText("SMTP from email")).toHaveValue("noreply@example.com");
        expect(screen.getByLabelText("Use STARTTLS")).toBeChecked();
        expect(screen.getByLabelText("Frontend base URL")).toHaveValue("https://app.env.example.com");
        expect(screen.getByLabelText("Backend base URL")).toHaveValue("https://api.env.example.com");
    });

    it("shows configured message when already initialized", () => {
        renderWizard(true);

        expect(screen.getByText("Application Already Configured")).toBeInTheDocument();
        expect(screen.getByText("Go to login")).toBeInTheDocument();
    });
});
