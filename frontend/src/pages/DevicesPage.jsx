import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
    WifiIcon,
    ComputerDesktopIcon,
    DevicePhoneMobileIcon,
    ShieldCheckIcon,
    ShieldExclamationIcon,
    ClockIcon,
    ArrowPathIcon,
    CheckBadgeIcon,
    XCircleIcon
} from '@heroicons/react/24/outline';

const DevicesPage = () => {
    const [devices, setDevices] = useState([
        {
            mac: "AA:BB:CC:DD:EE:FF",
            ip: "192.168.1.45",
            authenticated: true,
            hostname: "Skye's MacBook",
            deviceType: "laptop",
            lastSeen: "2 minutes ago",
            connectionTime: "1h 23m",
            upload: "15.2 MB",
            download: "45.8 MB"
        },
        {
            mac: "11:22:33:44:55:66",
            ip: "192.168.1.46",
            authenticated: false,
            hostname: "Unknown Device",
            deviceType: "unknown",
            lastSeen: "5 minutes ago",
            connectionTime: "0m",
            upload: "0 MB",
            download: "0 MB"
        },
        {
            mac: "FF:EE:DD:CC:BB:AA",
            ip: "192.168.1.47",
            authenticated: true,
            hostname: "Android Phone",
            deviceType: "mobile",
            lastSeen: "Just now",
            connectionTime: "45m",
            upload: "8.1 MB",
            download: "22.3 MB"
        }
    ]);

    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchDevices = async () => {
            try {
                setLoading(true);
                // const response = await axios.get('/status');
                // setDevices(response.data.connected_devices);
            } catch (error) {
                console.error('Error fetching devices:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchDevices();
    }, []);

    const handleGrantAccess = async (mac) => {
        try {
            setLoading(true);
            // await axios.post(`/admin/grant_access/${mac}`);
            setDevices(devices.map(device =>
                device.mac === mac ? { ...device, authenticated: true } : device
            ));
        } catch (error) {
            console.error('Error granting access:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleRevokeAccess = async (mac) => {
        try {
            setLoading(true);
            // await axios.post(`/admin/revoke_access/${mac}`);
            setDevices(devices.map(device =>
                device.mac === mac ? { ...device, authenticated: false } : device
            ));
        } catch (error) {
            console.error('Error revoking access:', error);
        } finally {
            setLoading(false);
        }
    };

    const getDeviceIcon = (deviceType) => {
        switch (deviceType) {
            case 'laptop':
                return <ComputerDesktopIcon className="w-6 h-6 text-blue-500" />;
            case 'mobile':
                return <DevicePhoneMobileIcon className="w-6 h-6 text-green-500" />;
            default:
                return <WifiIcon className="w-6 h-6 text-gray-500" />;
        }
    };

    const getStatusBadge = (authenticated) => {
        if (authenticated) {
            return (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    <ShieldCheckIcon className="w-3 h-3 mr-1" />
                    Authenticated
                </span>
            );
        } else {
            return (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                    <ShieldExclamationIcon className="w-3 h-3 mr-1" />
                    Blocked
                </span>
            );
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 dark:from-gray-900 dark:to-blue-900 p-4">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                                Connected Devices
                            </h1>
                            <p className="text-gray-600 dark:text-gray-300">
                                Manage and monitor devices on your network
                            </p>
                        </div>
                        <button
                            onClick={() => window.location.reload()}
                            className="flex items-center space-x-2 bg-white dark:bg-gray-800 px-4 py-2 rounded-lg shadow-md hover:shadow-lg transition-shadow"
                        >
                            <ArrowPathIcon className={`w-5 h-5 text-gray-600 ${loading ? 'animate-spin' : ''}`} />
                            <span>Refresh</span>
                        </button>
                    </div>
                </div>

                {/* Stats Overview */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-500 dark:text-gray-400">Total Devices</p>
                                <p className="text-2xl font-bold text-gray-900 dark:text-white">{devices.length}</p>
                            </div>
                            <WifiIcon className="w-8 h-8 text-blue-500" />
                        </div>
                    </div>

                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-500 dark:text-gray-400">Authenticated</p>
                                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                                    {devices.filter(d => d.authenticated).length}
                                </p>
                            </div>
                            <ShieldCheckIcon className="w-8 h-8 text-green-500" />
                        </div>
                    </div>

                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-500 dark:text-gray-400">Blocked</p>
                                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                                    {devices.filter(d => !d.authenticated).length}
                                </p>
                            </div>
                            <ShieldExclamationIcon className="w-8 h-8 text-red-500" />
                        </div>
                    </div>

                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-500 dark:text-gray-400">Active Now</p>
                                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                                    {devices.filter(d => d.lastSeen === 'Just now').length}
                                </p>
                            </div>
                            <ClockIcon className="w-8 h-8 text-purple-500" />
                        </div>
                    </div>
                </div>

                {/* Devices Table */}
                <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg overflow-hidden">
                    <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                            Network Devices
                        </h2>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-gray-50 dark:bg-gray-700">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                        Device
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                        Network Info
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                        Activity
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                        Status
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                        Actions
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200 dark:divide-gray-600">
                                {devices.map((device, index) => (
                                    <tr key={device.mac} className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center">
                                                <div className="flex-shrink-0">
                                                    {getDeviceIcon(device.deviceType)}
                                                </div>
                                                <div className="ml-4">
                                                    <div className="text-sm font-medium text-gray-900 dark:text-white">
                                                        {device.hostname}
                                                    </div>
                                                    <div className="text-sm text-gray-500 dark:text-gray-400">
                                                        {device.deviceType}
                                                    </div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm text-gray-900 dark:text-white font-mono">
                                                {device.ip}
                                            </div>
                                            <div className="text-sm text-gray-500 dark:text-gray-400 font-mono">
                                                {device.mac}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm text-gray-900 dark:text-white">
                                                Last seen: {device.lastSeen}
                                            </div>
                                            <div className="text-sm text-gray-500 dark:text-gray-400">
                                                Up: {device.upload} • Down: {device.download}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            {getStatusBadge(device.authenticated)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                            {device.authenticated ? (
                                                <button
                                                    onClick={() => handleRevokeAccess(device.mac)}
                                                    disabled={loading}
                                                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 transition-colors"
                                                >
                                                    <XCircleIcon className="w-4 h-4 mr-1" />
                                                    Revoke
                                                </button>
                                            ) : (
                                                <button
                                                    onClick={() => handleGrantAccess(device.mac)}
                                                    disabled={loading}
                                                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 transition-colors"
                                                >
                                                    <CheckBadgeIcon className="w-4 h-4 mr-1" />
                                                    Grant Access
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Empty State */}
                {devices.length === 0 && (
                    <div className="text-center py-12">
                        <WifiIcon className="mx-auto h-12 w-12 text-gray-400" />
                        <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No devices found</h3>
                        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                            No devices are currently connected to your network.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default DevicesPage;
