import {fireEvent, render, screen, waitFor} from "@testing-library/react";
import {beforeEach, describe, expect, it, vi} from "vitest";
import {MemoryRouter} from "react-router-dom";
import InitializedAppShell from "./InitializedAppShell";
import {AuthContext} from "../contexts/AuthContext";
import {fetchPublicBranding} from "../api/appConfig";

vi.mock("../hooks/useKeepUserLoggedIn.ts", () => ({
    useKeepUserLoggedIn: vi.fn(),
}));

vi.mock("../api/appConfig.ts", () => ({
    fetchPublicBranding: vi.fn(),
}));

vi.mock("../hooks/useT.ts", () => ({
    useT: (_key: string, _fillers?: Record<string, string>, fallback?: string) => fallback ?? _key,
}));

vi.mock("./UiLabel.tsx", () => ({
    default: ({k}: {k: string}) => <span>{k}</span>,
}));

vi.mock("./Register.tsx", () => ({default: () => <div>Register Page</div>}));
vi.mock("./Login.tsx", () => ({default: () => <div>Login Page</div>}));
vi.mock("./UserProfile.tsx", () => ({default: () => <div>Profile Page</div>}));
vi.mock("./Dashboard.tsx", () => ({default: () => <div>Dashboard Page</div>}));
vi.mock("./UserManagement.tsx", () => ({default: () => <div>User Management Page</div>}));
vi.mock("./ForgotPassword.tsx", () => ({default: () => <div>Forgot Password Page</div>}));
vi.mock("./ResetPassword.tsx", () => ({default: () => <div>Reset Password Page</div>}));
vi.mock("./AdminSettings.tsx", () => ({default: () => <div>Admin Settings Page</div>}));
vi.mock("./SetupWizard.tsx", () => ({default: () => <div>Setup Wizard Page</div>}));

function mockMatchMedia(matches: boolean) {
    const listeners = new Set<(event: MediaQueryListEvent) => void>();

    vi.stubGlobal("matchMedia", vi.fn().mockImplementation(() => ({
        matches,
        media: "(max-width: 767px)",
        onchange: null,
        addEventListener: (_event: string, callback: (event: MediaQueryListEvent) => void) => listeners.add(callback),
        removeEventListener: (_event: string, callback: (event: MediaQueryListEvent) => void) => listeners.delete(callback),
        addListener: (callback: (event: MediaQueryListEvent) => void) => listeners.add(callback),
        removeListener: (callback: (event: MediaQueryListEvent) => void) => listeners.delete(callback),
        dispatchEvent: vi.fn(),
    })));
}

function renderShell() {
    return render(
        <AuthContext.Provider
            value={{
                token: null,
                user: null,
                login: vi.fn(),
                register: vi.fn(),
                logout: vi.fn(),
                setToken: vi.fn(),
            }}
        >
            <MemoryRouter initialEntries={["/login"]}>
                <InitializedAppShell />
            </MemoryRouter>
        </AuthContext.Provider>,
    );
}

describe("InitializedAppShell", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        localStorage.clear();
        mockMatchMedia(true);
        vi.mocked(fetchPublicBranding).mockResolvedValue({
            appName: "ACE",
            siteLogo: null,
            backgroundImage: null,
        });
    });

    afterEach(() => {
        vi.unstubAllGlobals();
    });

    it("toggles the mobile guest navigation menu", async () => {
        renderShell();

        await waitFor(() => expect(screen.getByText("Login Page")).toBeInTheDocument());
        expect(screen.getAllByRole("link", {name: "nav.title.register"})).toHaveLength(1);

        fireEvent.click(screen.getByRole("button", {name: "Toggle navigation menu"}));

        expect(screen.getAllByRole("link", {name: "nav.title.register"})).toHaveLength(2);
        expect(screen.getAllByRole("link", {name: "nav.title.login"})).toHaveLength(2);
    });
});
