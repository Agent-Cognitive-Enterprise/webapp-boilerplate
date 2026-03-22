// frontend/src/contexts/AuthContext.tsx

import {createContext, useState, useEffect} from 'react';
import type {ReactNode} from 'react';
import {useNavigate} from 'react-router-dom';
import { subscribeToSessionInvalidation } from '../auth/sessionEvents.ts';
import {loginUser, fetchUserProfile, logoutUser, refreshUserSession, registerUser} from '../api/auth.ts';
import { getSavedUiLocalePreference } from '../api/userSettings.ts';
import { applyDocumentLocaleDirection, persistActiveUiLocale } from '../i18n/localeDirection.ts';

// Define types for user and context
interface User {
    full_name: string;
    email: string;
    id: string;
    is_admin: boolean;
    is_active: boolean;
}

interface AuthContextType {
    token: string | null;
    user: User | null;
    isLoading?: boolean;
    login: (username: string, password: string) => Promise<void>;
    register: (full_name: string, email: string, password: string) => Promise<void>;
    logout: () => void;
    setToken: (token: string | null) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
    children: ReactNode;
}

const AuthProvider = ({children}: AuthProviderProps) => {
    const [token, setToken] = useState<string | null>(null);
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const navigate = useNavigate();

    const clearAuthState = () => {
        setToken(null);
        setUser(null);
    };

    const hydrateStoredLocalePreference = async () => {
        const savedLocale = await getSavedUiLocalePreference();
        if (!savedLocale) {
            return;
        }
        const normalized = persistActiveUiLocale(savedLocale);
        applyDocumentLocaleDirection(normalized);
    };

    useEffect(() => {
        let active = true;

        const getUser = async () => {
            setIsLoading(true);
            try {
                let userData;
                try {
                    userData = await fetchUserProfile({ skipAuthRefresh: true });
                } catch {
                    await refreshUserSession();
                    userData = await fetchUserProfile({ skipAuthRefresh: true });
                }
                if (!active) {
                    return;
                }
                await hydrateStoredLocalePreference();
                setUser(userData);
                setToken('cookie-session');
            } catch {
                if (!active) {
                    return;
                }
                clearAuthState();
            } finally {
                if (active) {
                    setIsLoading(false);
                }
            }
        };

        void getUser();

        return () => {
            active = false;
        };
    }, []);

    useEffect(() => {
        return subscribeToSessionInvalidation(() => {
            clearAuthState();
            setIsLoading(false);
            navigate('/login');
        });
    }, [navigate]);

    const login = async (username: string, password: string) => {
        try {
            setIsLoading(true);
            await loginUser({username, password});
            const userProfile = await fetchUserProfile();
            await hydrateStoredLocalePreference();
            setToken('cookie-session');
            setUser(userProfile);
            navigate('/dashboard');
        } catch (err: any) {
            const status = err.response?.status;
            const detail = err.response?.data?.detail;
            // Re-throw with user-friendly message
            if (status === 401 || status === 400) {
                throw new Error('Invalid email or password');
            } else if (status === 403 && detail === 'Email verification required') {
                throw new Error('Email verification required. Please check your inbox.');
            } else if (status === 403) {
                throw new Error('Account is not active. Please contact support.');
            } else if (err.message) {
                throw err;
            } else {
                throw new Error('Login failed. Please try again.');
            }
        } finally {
            setIsLoading(false);
        }
    };

    const register = async (full_name: string, email: string, password: string) => {
        try {
            await registerUser({full_name, email, password});
            navigate('/login');
        } catch (err: any) {
            const status = err.response?.status;
            const detail = err.response?.data?.detail;

            if (status === 400 && typeof detail === "string") {
                throw new Error(detail);
            }
            if (err.message) {
                throw err;
            }
            throw new Error("Registration failed. Please try again.");
        }
    };

    const logout = async () => {
        try {
            await logoutUser();
        } catch (error) {
            console.error('Backend logout failed:', error);
        } finally {
            clearAuthState();
            navigate('/login');
        }
    };

    const setTokenInContext = (newToken: string | null) => {
        setToken(newToken ? 'cookie-session' : null);
    };

    return (
        <AuthContext.Provider value={{token, user, isLoading, login, register, logout, setToken: setTokenInContext}}>
            {children}
        </AuthContext.Provider>
    );
};

export {AuthProvider, AuthContext};
