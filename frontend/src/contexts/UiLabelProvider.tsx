// /frontend/src/contexts/UiLabelProvider.tsx

import React, {createContext, useContext} from "react";
import {AuthContext} from "./AuthContext";
import {useUiLabelStore} from "./uiLabels/useUiLabelStore";
import type {UiLabelContextType} from "./uiLabels/types";

const UiLabelCtx = createContext<UiLabelContextType | undefined>(undefined);

export const UiLabelProvider: React.FC<{ children: React.ReactNode }> = ({
                                                                             children,
                                                                         }) => {
    const auth = useContext(AuthContext);
    if (!auth) throw new Error("AuthContext not available");
    const {token} = auth;
    const ctxValue = useUiLabelStore(token);

    return <UiLabelCtx.Provider value={ctxValue}>{children}</UiLabelCtx.Provider>;
};

// eslint-disable-next-line react-refresh/only-export-components
export function useUiLabelContext(): UiLabelContextType {
    const ctx = useContext(UiLabelCtx);
    if (!ctx) throw new Error("UILabel provider is missing");
    return ctx;
}
