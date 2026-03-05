import {describe, it, expect, vi, beforeEach} from "vitest";
import {fireEvent, render, screen, waitFor} from "@testing-library/react";
import {MemoryRouter, Route, Routes} from "react-router-dom";

import AdminSettings from "./AdminSettings";
import {AuthContext} from "../contexts/AuthContext";
import {UiLabelProvider} from "../contexts/UiLabelProvider";
import {getAdminSettings, updateAdminSettings} from "../api/adminSettings";
import api from "../api/api";

vi.mock("../api/adminSettings", () => ({
    getAdminSettings: vi.fn(),
    updateAdminSettings: vi.fn(),
    checkAdminEmailSettings: vi.fn(),
}));
vi.mock("../api/api", () => ({
    default: {
        post: vi.fn(),
    },
}));

function renderAdminSettings(isAdmin: boolean) {
    const authValue = {
        token: "token-123",
        user: {is_admin: isAdmin},
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        setToken: vi.fn(),
    };
    return render(
        <AuthContext.Provider value={authValue as any}>
            <UiLabelProvider>
                <MemoryRouter initialEntries={["/admin/settings"]}>
                    <Routes>
                        <Route path="/admin/settings" element={<AdminSettings/>}/>
                        <Route path="/dashboard" element={<div>Dashboard Page</div>}/>
                    </Routes>
                </MemoryRouter>
            </UiLabelProvider>
        </AuthContext.Provider>
    );
}

describe("AdminSettings", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        localStorage.clear();
        vi.mocked(api.post).mockImplementation(async (_url: string, payload: any) => {
            if (payload?.action === "add") {
                return {data: {success: true, message: "scheduled for translation"}} as any;
            }
            if (payload?.action === "get") {
                if (payload.locale === "fr") {
                    return {
                        data: {
                            success: true,
                            data: {
                                locale: "fr",
                                values_hash: "hash-fr",
                                labels: {
                                    "setup.field.site_name": "Nom du site",
                                },
                            },
                        },
                    } as any;
                }
                if (payload.locale === "en") {
                    return {
                        data: {
                            success: true,
                            data: {
                                locale: "en",
                                values_hash: "hash-en",
                                labels: {
                                    "setup.field.site_name": "Site name",
                                    "setup.field.supported_locales": "Supported locales",
                                    "admin.settings.openai_api_key": "OpenAI API key",
                                    "admin.settings.save": "Save settings",
                                },
                            },
                        },
                    } as any;
                }
                if (payload.locale === "sk") {
                    return {
                        data: {
                            success: true,
                            data: {
                                locale: "sk",
                                values_hash: "hash-sk",
                                labels: {
                                    "dashboard.link.admin_settings": "Nastavenia správcu",
                                },
                            },
                        },
                    } as any;
                }
                return {
                    data: {
                        success: true,
                        data: {locale: payload.locale, values_hash: `hash-${payload.locale}`, labels: {}},
                    },
                } as any;
            }
            return {data: {success: true, data: {values_hash: "noop"}}} as any;
        });
    });

    it("redirects non-admin user", () => {
        renderAdminSettings(false);
        expect(screen.getByText("Dashboard Page")).toBeInTheDocument();
    });

    it("keeps hook order stable when auth state changes to admin", async () => {
        vi.mocked(getAdminSettings).mockResolvedValue({
            site_name: "ACE Site",
            default_locale: "en",
            supported_locales: ["en"],
            site_logo: null,
            background_image: null,
            openai_api_key_masked: null,
            deepseek_api_key_masked: null,
            admin_email: "admin@example.com",
            smtp_host: null,
            smtp_port: null,
            smtp_username: null,
            smtp_password_masked: "***...***",
            smtp_from_email: null,
            smtp_use_tls: true,
            auth_frontend_base_url: "https://app.example.com",
            auth_backend_base_url: "https://api.example.com",
            email_configured: false,
        });

        const nonAdminAuthValue = {
            token: "token-123",
            user: null,
            login: vi.fn(),
            register: vi.fn(),
            logout: vi.fn(),
            setToken: vi.fn(),
        };
        const adminAuthValue = {
            ...nonAdminAuthValue,
            user: {is_admin: true},
        };

        const view = render(
            <AuthContext.Provider value={nonAdminAuthValue as any}>
                <UiLabelProvider>
                    <MemoryRouter initialEntries={["/admin/settings"]}>
                        <AdminSettings/>
                    </MemoryRouter>
                </UiLabelProvider>
            </AuthContext.Provider>
        );

        expect(getAdminSettings).toHaveBeenCalledTimes(0);

        view.rerender(
            <AuthContext.Provider value={adminAuthValue as any}>
                <UiLabelProvider>
                    <MemoryRouter initialEntries={["/admin/settings"]}>
                        <AdminSettings/>
                    </MemoryRouter>
                </UiLabelProvider>
            </AuthContext.Provider>
        );

        await waitFor(() => expect(getAdminSettings).toHaveBeenCalledTimes(1));
        expect(screen.getByDisplayValue("ACE Site")).toBeInTheDocument();
    });

    it("does not redirect away from /admin/settings while auth user is still resolving", async () => {
        vi.mocked(getAdminSettings).mockResolvedValue({
            site_name: "ACE Site",
            default_locale: "en",
            supported_locales: ["en"],
            site_logo: null,
            background_image: null,
            openai_api_key_masked: null,
            deepseek_api_key_masked: null,
            admin_email: "admin@example.com",
            smtp_host: null,
            smtp_port: null,
            smtp_username: null,
            smtp_password_masked: "***...***",
            smtp_from_email: null,
            smtp_use_tls: true,
            auth_frontend_base_url: "https://app.example.com",
            auth_backend_base_url: "https://api.example.com",
            email_configured: false,
        });

        const loadingAuthValue = {
            token: "token-123",
            user: null,
            login: vi.fn(),
            register: vi.fn(),
            logout: vi.fn(),
            setToken: vi.fn(),
        };
        const adminAuthValue = {
            ...loadingAuthValue,
            user: {is_admin: true},
        };

        const view = render(
            <AuthContext.Provider value={loadingAuthValue as any}>
                <UiLabelProvider>
                    <MemoryRouter initialEntries={["/admin/settings"]}>
                        <Routes>
                            <Route path="/admin/settings" element={<AdminSettings/>}/>
                            <Route path="/dashboard" element={<div>Dashboard Page</div>}/>
                        </Routes>
                    </MemoryRouter>
                </UiLabelProvider>
            </AuthContext.Provider>
        );

        expect(screen.getByText("Loading admin settings...")).toBeInTheDocument();
        expect(screen.queryByText("Dashboard Page")).not.toBeInTheDocument();
        expect(getAdminSettings).toHaveBeenCalledTimes(0);

        view.rerender(
            <AuthContext.Provider value={adminAuthValue as any}>
                <UiLabelProvider>
                    <MemoryRouter initialEntries={["/admin/settings"]}>
                        <Routes>
                            <Route path="/admin/settings" element={<AdminSettings/>}/>
                            <Route path="/dashboard" element={<div>Dashboard Page</div>}/>
                        </Routes>
                    </MemoryRouter>
                </UiLabelProvider>
            </AuthContext.Provider>
        );

        await waitFor(() => expect(getAdminSettings).toHaveBeenCalledTimes(1));
        expect(screen.queryByText("Dashboard Page")).not.toBeInTheDocument();
        expect(screen.getByDisplayValue("ACE Site")).toBeInTheDocument();
    });

    it("loads and displays admin settings", async () => {
        vi.mocked(getAdminSettings).mockResolvedValue({
            site_name: "ACE Site",
            default_locale: "en",
            supported_locales: ["en", "fr"],
            site_logo: null,
            background_image: null,
            openai_api_key_masked: "sk-****1234",
            deepseek_api_key_masked: "ds-****5678",
            admin_email: "admin@example.com",
            smtp_host: null,
            smtp_port: null,
            smtp_username: null,
            smtp_password_masked: "***...***",
            smtp_from_email: null,
            smtp_use_tls: true,
            auth_frontend_base_url: "https://app.example.com",
            auth_backend_base_url: "https://api.example.com",
            email_configured: false,
        });

        renderAdminSettings(true);

        await waitFor(() => expect(getAdminSettings).toHaveBeenCalledTimes(1));
        expect(screen.getByDisplayValue("ACE Site")).toBeInTheDocument();
        expect(screen.getByDisplayValue("admin@example.com")).toBeInTheDocument();
        expect(screen.queryByText("Stored: sk-****1234")).not.toBeInTheDocument();
        const openAiInput = screen.getByLabelText("OpenAI API key") as HTMLInputElement;
        const deepSeekInput = screen.getByLabelText("DeepSeek API key") as HTMLInputElement;
        const adminPasswordInput = screen.getByLabelText("Admin password") as HTMLInputElement;
        const smtpPasswordInput = screen.getByLabelText("SMTP password") as HTMLInputElement;
        const frontendBaseUrlInput = screen.getByLabelText("Frontend base URL") as HTMLInputElement;
        const backendBaseUrlInput = screen.getByLabelText("Backend base URL") as HTMLInputElement;
        expect(openAiInput.type).toBe("password");
        expect(deepSeekInput.type).toBe("password");
        expect(adminPasswordInput.type).toBe("password");
        expect(smtpPasswordInput.type).toBe("password");
        expect(openAiInput.value).toBe("sk-****1234");
        expect(deepSeekInput.value).toBe("ds-****5678");
        expect(adminPasswordInput.value).toBe("********");
        expect(smtpPasswordInput.value).toBe("********");
        expect(frontendBaseUrlInput.value).toBe("https://app.example.com");
        expect(backendBaseUrlInput.value).toBe("https://api.example.com");
    });

    it("uses uiLocale directly for admin settings translations even when locale is not in setup locale list", async () => {
        localStorage.setItem("uiLocale", "sk");
        vi.mocked(getAdminSettings).mockResolvedValue({
            site_name: "ACE Site",
            default_locale: "en",
            supported_locales: ["en", "sk"],
            site_logo: null,
            background_image: null,
            openai_api_key_masked: null,
            deepseek_api_key_masked: null,
            admin_email: "admin@example.com",
            smtp_host: null,
            smtp_port: null,
            smtp_username: null,
            smtp_password_masked: null,
            smtp_from_email: null,
            smtp_use_tls: true,
            auth_frontend_base_url: null,
            auth_backend_base_url: null,
            email_configured: false,
        });

        renderAdminSettings(true);

        await waitFor(() => expect(getAdminSettings).toHaveBeenCalledTimes(1));
        expect(await screen.findByRole("heading", {name: "Nastavenia správcu"})).toBeInTheDocument();
    });

    it("keeps user-selected uiLocale instead of forcing backend default_locale", async () => {
        localStorage.setItem("uiLocale", "ru");
        vi.mocked(getAdminSettings).mockResolvedValue({
            site_name: "ACE Site",
            default_locale: "sk",
            supported_locales: ["en", "sk"],
            site_logo: null,
            background_image: null,
            openai_api_key_masked: null,
            deepseek_api_key_masked: null,
            admin_email: "admin@example.com",
            smtp_host: null,
            smtp_port: null,
            smtp_username: null,
            smtp_password_masked: null,
            smtp_from_email: null,
            smtp_use_tls: true,
            auth_frontend_base_url: null,
            auth_backend_base_url: null,
            email_configured: false,
        });

        renderAdminSettings(true);

        await waitFor(() => expect(getAdminSettings).toHaveBeenCalledTimes(1));
        await waitFor(() => expect(localStorage.getItem("uiLocale")).toBe("ru"));
    });

    it("submits updated settings", async () => {
        const reloadSpy = vi.fn();
        vi.stubGlobal("location", {
            ...window.location,
            reload: reloadSpy,
        });
        vi.mocked(getAdminSettings).mockResolvedValue({
            site_name: "ACE Site",
            default_locale: "en",
            supported_locales: ["en"],
            site_logo: null,
            background_image: null,
            openai_api_key_masked: null,
            deepseek_api_key_masked: null,
            admin_email: "admin@example.com",
            smtp_host: null,
            smtp_port: null,
            smtp_username: null,
            smtp_password_masked: null,
            smtp_from_email: null,
            smtp_use_tls: true,
            auth_frontend_base_url: null,
            auth_backend_base_url: null,
            email_configured: false,
        });
        vi.mocked(updateAdminSettings).mockResolvedValue({
            site_name: "ACE Site 2",
            default_locale: "en",
            supported_locales: ["en"],
            site_logo: null,
            background_image: null,
            openai_api_key_masked: "sk-****0000",
            deepseek_api_key_masked: null,
            admin_email: "admin@example.com",
            smtp_host: null,
            smtp_port: null,
            smtp_username: null,
            smtp_password_masked: null,
            smtp_from_email: null,
            smtp_use_tls: true,
            auth_frontend_base_url: null,
            auth_backend_base_url: null,
            email_configured: false,
        });

        renderAdminSettings(true);
        await waitFor(() => expect(getAdminSettings).toHaveBeenCalledTimes(1));

        const siteNameInput = await screen.findByLabelText("Site name");
        const openAiInput = await screen.findByLabelText("OpenAI API key");
        const saveButton = await screen.findByRole("button", {name: "Save settings"});

        fireEvent.change(siteNameInput, {target: {value: "ACE Site 2"}});
        fireEvent.change(openAiInput, {target: {value: "sk-new-key-0000"}});
        fireEvent.click(saveButton);

        await waitFor(() => expect(updateAdminSettings).toHaveBeenCalledTimes(1));
        expect(vi.mocked(updateAdminSettings).mock.calls[0][0]).toMatchObject({
            site_name: "ACE Site 2",
            supported_locales: ["en"],
            openai_api_key: "sk-new-key-0000",
            admin_email: "admin@example.com",
        });
        expect(reloadSpy).toHaveBeenCalledTimes(1);
        vi.unstubAllGlobals();
    });

    it("updates supported locales text input", async () => {
        vi.mocked(getAdminSettings).mockResolvedValue({
            site_name: "ACE Site",
            default_locale: "en",
            supported_locales: ["en", "fr"],
            site_logo: null,
            background_image: null,
            openai_api_key_masked: null,
            deepseek_api_key_masked: null,
            admin_email: "admin@example.com",
            smtp_host: null,
            smtp_port: null,
            smtp_username: null,
            smtp_password_masked: null,
            smtp_from_email: null,
            smtp_use_tls: true,
            auth_frontend_base_url: null,
            auth_backend_base_url: null,
            email_configured: false,
        });

        renderAdminSettings(true);
        await waitFor(() => expect(getAdminSettings).toHaveBeenCalledTimes(1));

        const supportedInput = await screen.findByLabelText("Supported locales") as HTMLInputElement;
        fireEvent.change(supportedInput, {target: {value: "en, fr, de"}});
        expect(supportedInput.value).toBe("en, fr, de");
    });

    it("schedules missing admin-settings labels for translation through ui-label add flow", async () => {
        vi.mocked(getAdminSettings).mockResolvedValue({
            site_name: "ACE Site",
            default_locale: "en",
            supported_locales: ["en"],
            site_logo: null,
            background_image: null,
            openai_api_key_masked: null,
            deepseek_api_key_masked: null,
            admin_email: "admin@example.com",
            smtp_host: null,
            smtp_port: null,
            smtp_username: null,
            smtp_password_masked: null,
            smtp_from_email: null,
            smtp_use_tls: true,
            auth_frontend_base_url: null,
            auth_backend_base_url: null,
            email_configured: false,
        });

        renderAdminSettings(true);
        await waitFor(() => expect(getAdminSettings).toHaveBeenCalledTimes(1));

        await waitFor(() => {
            expect(vi.mocked(api.post).mock.calls.some(([, payload]) =>
                payload?.action === "add"
                && payload?.locale === "en"
                && payload?.key === "admin.settings.ai_keys",
            )).toBe(true);
        });
    });
});
