import React, { useState, useEffect } from 'react';
import {
    Snackbar,
    Alert,
} from '@mui/material';

const AlertUser = ({ message, type = "success", duration = 5000 }) => {
    const [open, setOpen] = useState(false);
    const [autoHideDuration, setautoHideDuration] = useState(5000)

    useEffect(() => {
        setOpen(true)
        setautoHideDuration(duration)
    }, [autoHideDuration]);

    const handleClose = () => {
        setOpen(false);
    };


    return (
        <>
            <Snackbar
                open={open}
                autoHideDuration={autoHideDuration}
                className='z-30'
                onClose={handleClose}
                anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
            >
                <Alert severity={type} onClose={handleClose}>
                    {message}
                </Alert>
            </Snackbar>
        </>
    );
};

export default AlertUser;
