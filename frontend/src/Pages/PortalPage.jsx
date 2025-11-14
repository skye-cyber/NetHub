import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Button, Typography, Container, Paper } from '@mui/material';
import axios from 'axios';

const PortalPage = ({}) => {
  const [clientInfo, setClientInfo] = useState({ ip: '', mac: '' });
  const navigate = useNavigate();

  const handleConnect = async () => {
    try {
      const response = await axios.post('/connect');
      if (response.data.status === 'success') {
        navigate(response.data.redirect_url);
      } else {
        alert(response.data.message);
      }
    } catch (error) {
      console.error('Connection error:', error);
      alert('Failed to connect to the network');
    }
  };

  return (
    <Container maxWidth="sm">
      <Paper elevation={3} sx={{ p: 4, mt: 8 }}>
        <Typography variant="h4" component="h1" gutterBottom align="center">
          Network Hub Portal
        </Typography>
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
          >
            Connect to Network
          </Button>
        </Box>
      </Paper>
    </Container>
  );
};

export default PortalPage;
