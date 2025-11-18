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

const DevicePage = () => {
    const [devices, setDevices] = useState([{ mac: "00:00:00:00", ip: "192.168.234.34", authenticated: false, auth: "Blocked" }]);

    useEffect(() => {
        const fetchDevices = async () => {
            try {
                const response = await axios.get('/status');
                //setDevices(response.data.connected_devices);
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
        <>
            <title>Devices</title>
            <Container className='w-full max-w-full' maxWidth="lg">
                <Paper className='shadow-none xs:shaddow-md w-full p-1 mt-1 xs:mt-4 xs:p-4 bg-white dark:bg-gray-200' elevation={3}>
                    <TableContainer component={Paper} sx={{ mt: 4 }}>
                        <Table>
                            <TableHead className='bg-white dark:bg-gray-300 text-gray-800 dark:text-gray-100 shadow-none'>
                                <TableRow>
                                    <TableCell className='font-[500]'>MAC Address</TableCell>
                                    <TableCell className='font-[500]'>IP Address</TableCell>
                                    <TableCell className='font-[500]'>Status</TableCell>
                                    <TableCell className='font-[500]'>Actions</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {devices?.map((device) => (
                                    <TableRow className='bg-white dark:bg-gray-300/70' key={device.mac}>
                                        <TableCell>{device.mac}</TableCell>
                                        <TableCell>{device.ip}</TableCell>
                                        <TableCell
                                            className={
                                                device?.auth?.toLocaleLowerCase() === "blocked" ? 'text-red-400'
                                                    : (device?.auth?.toLocaleLowerCase() === 'authenticated' ? 'text-green-400' : 'text-blue-400'
                                                    )}>
                                            {device?.authenticated ? 'Authenticated' : 'Blocked'}
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
        </>
    );
};

export default DevicePage;
