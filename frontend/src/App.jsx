import React from 'react';
//import logo from './logo.svg';
import './styles/App.css';
import './styles/styles.css';
import { MainLayout } from './components/Layout/MainLayout';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import PortalPage from './pages/PortalPage';
import DashboardPage from './pages/DashboardPage';
import AdminPage from './pages/AdminPage';
import ConnectionStatus from './components/ConnectionStatus';

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

const App  = () => {
    return (
        <MainLayout>
            <ThemeProvider theme={theme}>
                <CssBaseline />
                <ConnectionStatus />
                <Router>
                    <Routes>
                        <Route path="/" element={<PortalPage />} />
                        <Route path="/dashboard" element={<DashboardPage />} />
                        <Route path="/admin" element={<AdminPage />} />
                    </Routes>
                </Router>
            </ThemeProvider>
        </MainLayout>
    );
}

export default App;
