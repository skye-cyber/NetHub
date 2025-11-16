import React, { useState, useEffect } from 'react';
import { Typography, Container, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Button } from '@mui/material';
import axios from 'axios';

/*
interface Device {
    mac: string;
    ip: string;
    authenticated: boolean;
}
*/

const AdminPage = () => {
    const [devices, setDevices] = useState([]);

    useEffect(() => {
        const fetchDevices = async () => {
            try {
                const response = await axios.get('/status');
                setDevices(response.data.connected_devices);
            } catch (error) {
                console.error('Error fetching devices:', error);
            }
        };

        fetchDevices();
    }, []);

    const handleGrantAccess = async (mac) => {
        try {
            await axios.post(`/admin/grant_access/${mac}`);
            setDevices(devices.map(device =>
                device.mac === mac ? { ...device, authenticated: true } : device
            ));
        } catch (error) {
            console.error('Error granting access:', error);
        }
    };

    const handleRevokeAccess = async (mac) => {
        try {
            await axios.post(`/admin/revoke_access/${mac}`);
            setDevices(devices.map(device =>
                device.mac === mac ? { ...device, authenticated: false } : device
            ));
        } catch (error) {
            console.error('Error revoking access:', error);
        }
    };

    return (
        <Container maxWidth="lg">
            <Paper elevation={3} sx={{ p: 4, mt: 8 }}>
                <Typography variant="h4" component="h1" gutterBottom align="center">
                    Network Hub Admin Panel
                </Typography>
                <TableContainer component={Paper} sx={{ mt: 4 }}>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>MAC Address</TableCell>
                                <TableCell>IP Address</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell>Actions</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {devices.map((device) => (
                                <TableRow key={device.mac}>
                                    <TableCell>{device.mac}</TableCell>
                                    <TableCell>{device.ip}</TableCell>
                                    <TableCell>
                                        {device.authenticated ? 'Authenticated' : 'Blocked'}
                                    </TableCell>
                                    <TableCell>
                                        {device.authenticated ? (
                                            <Button
                                                variant="contained"
                                                color="error"
                                                onClick={() => handleRevokeAccess(device.mac)}
                                            >
                                                Revoke Access
                                            </Button>
                                        ) : (
                                            <Button
                                                variant="contained"
                                                color="success"
                                                onClick={() => handleGrantAccess(device.mac)}
                                            >
                                                Grant Access
                                            </Button>
                                        )}
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            </Paper>
        </Container>
    );
};

export default AdminPage;
