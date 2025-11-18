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
            <title>Admin</title>
            <Container className='w-full max-w-full' maxWidth="lg">
            {/* TODO: add dark mode support with elegant appearnce on both themes
                implement registration of new networks:
                1. existing networks
                2. create new network eg hostpot
                user management
                user priviledge management(use least priviledge)
                generation of direct access codes,
                devices history etc
                ...other network administrative tasks
                */
            }
            </Container>
        </>
    );
};

export default AdminPage;
