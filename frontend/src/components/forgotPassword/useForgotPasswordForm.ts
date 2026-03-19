import {useState} from "react";
import api from "../../api/api";

export function useForgotPasswordForm() {
    const [email, setEmail] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setError(null);
        setIsLoading(true);

        try {
            await api.post("/auth/forgot-password", {email});
            setSuccess(true);
        } catch (err: any) {
            if (err?.response?.status === 404) {
                setSuccess(true);
                return;
            }

            setError("Failed to send reset email. Please try again.");
        } finally {
            setIsLoading(false);
        }
    };

    return {
        email,
        setEmail,
        isLoading,
        success,
        error,
        handleSubmit,
    };
}
