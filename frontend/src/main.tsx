// /frontend/src/main.tsx

import {createRoot} from 'react-dom/client';
import {BrowserRouter as Router} from 'react-router-dom';
import './index.css';
import App from './App.tsx';
import {AuthProvider} from './contexts/AuthContext';
import {UiLabelProvider} from './contexts/UiLabelProvider.tsx';
import {initializeDocumentTitle} from "./api/appConfig.ts";

void initializeDocumentTitle();

createRoot(document.getElementById('root')!).render(
    <Router>
        <AuthProvider>
            <UiLabelProvider>
                <App/>
            </UiLabelProvider>
        </AuthProvider>
    </Router>
);
