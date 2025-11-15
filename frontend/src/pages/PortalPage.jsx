import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Button, Typography, Container, Paper, Alert, CircularProgress } from '@mui/material';
import { connectToNetwork } from '../services/api';

const PortalPage = () => {
    const [clientInfo, setClientInfo] = useState({ ip: '192.168.x.x', mac: '00:00:00:00:00:00' });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    // Simulate getting client info if backend is unavailable
    useEffect(() => {
        // This would normally come from backend, but we have fallbacks
        const simulatedIp = localStorage.getItem('client_ip') || '192.168.12.1';
        const simulatedMac = localStorage.getItem('client_mac') || '00:00:00:00:00:00';
        setClientInfo({ ip: simulatedIp, mac: simulatedMac });
    }, []);

    const handleConnect = async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await connectToNetwork();
            if (response.data.status === 'success') {
                navigate(response.data.redirect_url);
            } else {
                setError(response.data.message);
            }
        } catch (err) {
            if (err.status === 'network_error') {
                setError('Server unavailable. Please check your connection or try again later.');

                // Store attempt for when connection is restored
                localStorage.setItem('pending_connection', 'true');
            } else {
                setError(err.message || 'Failed to connect to the network');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container maxWidth="sm">
            <Paper elevation={3} sx={{ p: 4, mt: 8 }}>
                <Typography variant="h4" component="h1" gutterBottom align="center">
                    Network Hub Portal
                </Typography>

                {error && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                        {error}
                    </Alert>
                )}

                <Typography variant="body1" gutterBottom>
                    Your IP: {clientInfo.ip}
                </Typography>
                <Typography variant="body1" gutterBottom>
                    Your MAC: {clientInfo.mac}
                </Typography>

                <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
                    <Button
                        variant="contained"
                        color="primary"
                        size="large"
                        onClick={handleConnect}
                        disabled={loading}
                    >
                        {loading ? <CircularProgress size={24} /> : 'Connect to Network'}
                    </Button>
                </Box>

                <Typography variant="body2" color="text.secondary" sx={{ mt: 2, textAlign: 'center' }}>
                    {process.env.NODE_ENV === 'development' ?
                        'Development mode - some features may be simulated' :
                        '© Network Hub'}
                </Typography>
            </Paper>
        </Container>
    );
};

export default PortalPage;
