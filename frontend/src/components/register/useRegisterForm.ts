import {useContext, useState} from "react";
import {AuthContext} from "../../contexts/AuthContext.tsx";
import {useT} from "../../hooks/useT.ts";

type RegisterContextValue = {
    register: (fullName: string, email: string, password: string) => Promise<void>;
};

export function useRegisterForm() {
    const [formData, setFormData] = useState({
        full_name: "",
        email: "",
        password: "",
    });
    const [error, setError] = useState<string | null>(null);
    const {register} = useContext(AuthContext) as RegisterContextValue;

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (error) {
            setError(null);
        }

        setFormData((current) => ({
            ...current,
            [event.target.name]: event.target.value,
        }));
    };

    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setError(null);

        try {
            await register(formData.full_name, formData.email, formData.password);
        } catch (err: any) {
            setError(err?.message || "Registration failed. Please try again.");
        }
    };

    return {
        formData,
        error,
        handleChange,
        handleSubmit,
        placeholderEnterYourFullName: useT("register.placeholder.enter_your_full_name"),
        placeholderEnterYourEmail: useT("register.placeholder.enter_your_email"),
        placeholderEnterYourPassword: useT("register.placeholder.enter_your_password"),
    };
}
