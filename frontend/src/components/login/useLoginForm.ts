import {useContext, useState} from "react";
import {AuthContext} from "../../contexts/AuthContext.tsx";
import {useT} from "../../hooks/useT.ts";

type LoginContextValue = {
    login: (email: string, password: string) => Promise<void>;
};

export function useLoginForm() {
    const [formData, setFormData] = useState({email: "", password: ""});
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const {login} = useContext(AuthContext) as LoginContextValue;

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setFormData((current) => ({
            ...current,
            [event.target.name]: event.target.value,
        }));

        if (error) {
            setError(null);
        }
    };

    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setError(null);
        setIsLoading(true);

        try {
            await login(formData.email, formData.password);
        } catch (err: any) {
            console.error("Login error:", err);
            setError(err.message || "Login failed. Please check your credentials.");
        } finally {
            setIsLoading(false);
        }
    };

    return {
        formData,
        error,
        isLoading,
        handleChange,
        handleSubmit,
        placeholderEnterYourEmail: useT("login.placeholder.enter_your_email"),
        placeholderEnterYourPassword: useT("login.placeholder.enter_your_password"),
    };
}
