import React from 'react';
//import logo from './logo.svg';
import './styles/App.css';
import './styles/styles.css';
import { MainLayout } from './components/Layout/MainLayout';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import CaptivePage from './pages/CaptivePortalPage';
import DashboardPage from './pages/DashboardPage';
import AdminPage from './pages/AdminPage';
import ConnectionStatus from './components/ConnectionStatus';
import Navigation from './components/Navigation/navigation';
import DevicePage from './pages/DevicesPage'
import DiscoverPage from './pages/DiscoverPage';
import SettingsPage from './pages/SettingsPage';
import PaymentPage from './pages/Payments';

const theme = createTheme({
    palette: {
        primary: {
            main: '#1976d2',
        },
        secondary: {
            main: '#dc004e',
        },
    },
});

const App = () => {
    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <MainLayout>
                <ThemeProvider theme={theme}>
                    <CssBaseline />
                    <ConnectionStatus />
                    <Router>
                        <Navigation />
                        <Routes>
                            <Route path="/" element={<PaymentPage />} />
                            <Route path="/dashboard" element={<DashboardPage />} />
                            <Route path="/admin" element={<AdminPage />} />
                            <Route path="/networks" element={<AdminPage />} />
                            <Route path="/captive" element={<CaptivePage />} />
                            <Route path="/devices" element={<DevicePage />} />
                            <Route path="/settings" element={<SettingsPage />} />
                            <Route path="/discover" element={<DiscoverPage />} />
                            <Route path="/payment" element={<PaymentPage />} />
                        </Routes>
                    </Router>
                </ThemeProvider>
            </MainLayout>
        </div>
    );
}

export default App;
