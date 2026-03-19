import {useState} from "react";
import {useNavigate} from "react-router-dom";
import api from "../../api/api";
import {useT} from "../../hooks/useT.ts";

type UseResetPasswordFormArgs = {
    token: string | null;
};

export function useResetPasswordForm({token}: UseResetPasswordFormArgs) {
    const navigate = useNavigate();
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setError(null);

        if (password !== confirmPassword) {
            setError("Passwords do not match");
            return;
        }

        if (!token) {
            setError("Invalid reset token");
            return;
        }

        setIsLoading(true);

        try {
            await api.post("/auth/reset-password", {
                token,
                new_password: password,
            });
            navigate("/login?reset=success");
        } catch (err: any) {
            const detail = err.response?.data?.detail;

            if (typeof detail === "object" && detail.message) {
                const errors = detail.errors || [];
                setError(`${detail.message}: ${errors.join(", ")}`);
            } else {
                setError(detail || "Failed to reset password. Please try again.");
            }
        } finally {
            setIsLoading(false);
        }
    };

    return {
        password,
        setPassword,
        confirmPassword,
        setConfirmPassword,
        isLoading,
        error,
        handleSubmit,
        placeholderPassword: useT("reset_password.placeholder.new_password"),
        placeholderConfirmPassword: useT("reset_password.placeholder.confirm_password"),
    };
}
