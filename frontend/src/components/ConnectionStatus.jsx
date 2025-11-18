import React, { useState, useEffect } from 'react';
import { Snackbar, Alert } from '@mui/material';
import { getStatus } from '../services/api';

const ConnectionStatus = () => {
    const [open, setOpen] = useState(false);
    const [status, setStatus] = useState('unknown');

    useEffect(() => {
        const checkConnection = async () => {
            try {
                const status = await getStatus();
                setStatus('online');
            } catch (error) {
                console.log(error)
                setStatus('offline');
                setOpen(true);
            }
        };

        // Check immediately
        checkConnection();

        // Then check periodically
        const interval = setInterval(checkConnection, 30000);

        return () => clearInterval(interval);
    }, [setStatus]);

    const handleClose = () => {
        setOpen(false);
    };

    return (
        <>
            {status === 'offline' && (
                <Snackbar
                    open={open}
                    autoHideDuration={null}
                    onClose={handleClose}
                    anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
                >
                    <Alert severity="warning" onClose={handleClose}>
                        Offline mode - Some features may be limited
                    </Alert>
                </Snackbar>
            )}
        </>
    );
};

export default ConnectionStatus;
