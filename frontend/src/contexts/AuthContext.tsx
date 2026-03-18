// frontend/src/contexts/AuthContext.tsx

import {createContext, useState, useEffect} from 'react';
import type {ReactNode} from 'react';
import {useNavigate} from 'react-router-dom';
import { subscribeToSessionInvalidation } from '../auth/sessionEvents.ts';
import { clearAccessToken, getAccessToken, setAccessToken } from '../auth/tokenStore.ts';
import {loginUser, fetchUserProfile, registerUser, logoutUser} from '../api/auth.ts';

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
    const [token, setToken] = useState<string | null>(getAccessToken());
    const [user, setUser] = useState<User | null>(null);
    const navigate = useNavigate();

    const clearAuthState = () => {
        setToken(null);
        setUser(null);
        clearAccessToken();
    };

    useEffect(() => {
        if (token) {
            const getUser = async () => {
                try {
                    const userData = await fetchUserProfile();
                    setUser(userData);
                } catch (err) {
                    console.error('Failed to fetch user profile:', err);
                    clearAuthState();
                    navigate('/login');
                }
            };
            void getUser();
        } else {
            setUser(null);
        }
    }, [navigate, token]);

    useEffect(() => {
        return subscribeToSessionInvalidation(() => {
            clearAuthState();
            navigate('/login');
        });
    }, [navigate]);

    const login = async (username: string, password: string) => {
        try {
            const response = await loginUser({username, password});
            if (response?.access_token) {
                setAccessToken(response.access_token);
                setToken(response.access_token);
                const userProfile = await fetchUserProfile();
                setUser(userProfile);
                navigate('/dashboard');
            } else {
                throw new Error('Invalid response from server');
            }
        } catch (err: any) {
            // Re-throw with user-friendly message
            if (err.response?.status === 401 || err.response?.status === 400) {
                throw new Error('Invalid email or password');
            } else if (err.response?.status === 403) {
                throw new Error('Account is not active. Please contact support.');
            } else if (err.message) {
                throw err;
            } else {
                throw new Error('Login failed. Please try again.');
            }
        }
    };

    const register = async (full_name: string, email: string, password: string) => {
        await registerUser({full_name, email, password});
        navigate('/login');
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
        setToken(newToken);
        if (newToken) setAccessToken(newToken);
        else clearAccessToken();
    };

    return (
        <AuthContext.Provider value={{token, user, login, register, logout, setToken: setTokenInContext}}>
            {children}
        </AuthContext.Provider>
    );
};

export {AuthProvider, AuthContext};
