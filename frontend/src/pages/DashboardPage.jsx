import React from 'react';
import { useLocation } from 'react-router-dom';
import { Box, Typography, Container, Paper } from '@mui/material';

const DashboardPage = () => {
    const location = useLocation();
    const searchParams = new URLSearchParams(location.search);
    const clientIp = searchParams.get('ip') || 'Unknown';
    const clientMac = searchParams.get('mac') || 'Unknown';

    return (
        <Container maxWidth="sm">
            <Paper elevation={3} sx={{ p: 4, mt: 8 }}>
                <Typography variant="h4" component="h1" gutterBottom align="center">
                    Network Hub Dashboard
                </Typography>
                <Typography variant="body1" gutterBottom>
                    Your IP: {clientIp}
                </Typography>
                <Typography variant="body1" gutterBottom>
                    Your MAC: {clientMac}
                </Typography>
                <Box sx={{ mt: 4 }}>
                    <Typography variant="body1">
                        You are now connected to the network!
                    </Typography>
                </Box>
            </Paper>
        </Container>
    );
};

export default DashboardPage;
