import { useState, useEffect } from 'react';
import {
    getDevices,
    grantAccess,
    revokeAccess,
} from '../services/api';
import {
    WifiIcon,
    ComputerDesktopIcon,
    DevicePhoneMobileIcon,
    ShieldCheckIcon,
    ShieldExclamationIcon,
    ClockIcon,
    ArrowPathIcon,
    CheckBadgeIcon,
    XCircleIcon,
    CpuChipIcon,
} from '@heroicons/react/24/outline';

const DevicesPage = () => {
    const [devices, setDevices] = useState([
        {
            mac: 'AA:BB:CC:DD:EE:FF',
            ip: '192.168.1.45',
            authenticated: true,
            hostname: "Skye's MacBook",
            deviceType: 'laptop',
            lastSeen: '2 minutes ago',
            connectionTime: '1h 23m',
            upload: '15.2 MB',
            download: '45.8 MB',
        },
        {
            mac: '11:22:33:44:55:66',
            ip: '192.168.1.46',
            authenticated: false,
            hostname: 'Unknown Device',
            deviceType: 'unknown',
            lastSeen: '5 minutes ago',
            connectionTime: '0m',
            upload: '0 MB',
            download: '0 MB',
        },
        {
            mac: 'FF:EE:DD:CC:BB:AA',
            ip: '192.168.1.47',
            authenticated: true,
            hostname: 'Android Phone',
            deviceType: 'mobile',
            lastSeen: 'Just now',
            connectionTime: '45m',
            upload: '8.1 MB',
            download: '22.3 MB',
        },
    ]);

    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchDevices = async () => {
            try {
                setLoading(true);
                const response = await getDevices();
                setDevices(response.data.connected_devices);
            } catch (error) {
                console.error('Error fetching devices:', error);
            } finally {
                setLoading(false);
            }
        };
        // fetchDevices();
    }, []);

    const handleGrantAccess = async (mac: string) => {
        try {
            setLoading(true);
            // await grantAccess(mac);
            setDevices((prev) =>
                prev.map((d) => (d.mac === mac ? { ...d, authenticated: true } : d))
            );
        } catch (error) {
            console.error('Error granting access:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleRevokeAccess = async (mac: string) => {
        try {
            setLoading(true);
            // await revokeAccess(mac);
            setDevices((prev) =>
                prev.map((d) => (d.mac === mac ? { ...d, authenticated: false } : d))
            );
        } catch (error) {
            console.error('Error revoking access:', error);
        } finally {
            setLoading(false);
        }
    };

    const getDeviceIcon = (type: string) => {
        const iconClass = 'w-5 h-5';
        switch (type) {
            case 'laptop':
                return <ComputerDesktopIcon className={`${iconClass} text-neo-primary`} />;
            case 'mobile':
                return <DevicePhoneMobileIcon className={`${iconClass} text-cyber-400`} />;
            case 'iot':
                return <CpuChipIcon className={`${iconClass} text-neo-secondary`} />;
            default:
                return <WifiIcon className={`${iconClass} text-neo-dim`} />;
        }
    };

    const stats = {
        total: devices.length,
        authenticated: devices.filter((d) => d.authenticated).length,
        blocked: devices.filter((d) => !d.authenticated).length,
        active: devices.filter((d) => d.lastSeen === 'Just now').length,
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 dark:from-neo-darker dark:to-neo-dark transition-colors duration-300 p-4 sm:p-6">
            {/* Ambient background glows */}
            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute -top-40 -right-40 h-96 w-96 rounded-full bg-neo-primary/5 blur-3xl" />
                <div className="absolute bottom-0 left-0 h-80 w-80 rounded-full bg-neo-secondary/5 blur-3xl" />
            </div>

            <div className="relative max-w-7xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex flex-wrap items-center justify-between gap-4">
                    <div>
                        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
                            <span className="bg-gradient-to-r from-neo-primary via-neo-secondary to-neo-accent bg-clip-text text-transparent">
                                Connected
                            </span>
                            <span className="text-gray-900 dark:text-neo-text"> Devices</span>
                        </h1>
                        <p className="text-gray-500 dark:text-neo-dim text-sm sm:text-base mt-1">
                            Manage and monitor devices on your network
                        </p>
                    </div>
                    <button
                        onClick={() => window.location.reload()}
                        className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white dark:bg-neo-dark/50 backdrop-blur-sm border border-gray-200 dark:border-neo-primary/30 text-gray-700 dark:text-neo-text shadow-md hover:shadow-lg dark:hover:shadow-neo transition-all duration-300"
                    >
                        <ArrowPathIcon className={`w-5 h-5 text-neo-primary ${loading ? 'animate-spin' : ''}`} />
                        <span className="text-sm font-medium">Refresh</span>
                    </button>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {[
                        { label: 'Total Devices', value: stats.total, icon: WifiIcon, color: 'neo-primary' },
                        { label: 'Authenticated', value: stats.authenticated, icon: ShieldCheckIcon, color: 'green' },
                        { label: 'Blocked', value: stats.blocked, icon: ShieldExclamationIcon, color: 'red' },
                        { label: 'Active Now', value: stats.active, icon: ClockIcon, color: 'neo-accent' },
                    ].map((stat, idx) => {
                        const Icon = stat.icon;
                        const isNeo = stat.color.startsWith('neo');
                        const colorClass = isNeo
                            ? `bg-${stat.color}/10 border-${stat.color}/30 text-${stat.color}`
                            : stat.color === 'green'
                                ? 'bg-green-500/10 border-green-500/30 text-green-500 dark:text-green-400'
                                : 'bg-red-500/10 border-red-500/30 text-red-500 dark:text-red-400';
                        return (
                            <div
                                key={idx}
                                className="group relative overflow-hidden rounded-xl bg-white dark:bg-neo-dark/60 backdrop-blur-sm border border-gray-200 dark:border-neo-primary/20 p-5 transition-all duration-300 hover:border-neo-primary/40 dark:hover:border-neo-primary/40 shadow-md dark:shadow-lg hover:shadow-lg dark:hover:shadow-neo"
                            >
                                <div className="absolute inset-0 bg-gradient-to-br from-neo-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                                <div className="relative flex items-center justify-between">
                                    <div>
                                        <p className="text-xs font-medium text-gray-500 dark:text-neo-dim uppercase tracking-wider">
                                            {stat.label}
                                        </p>
                                        <p className="text-2xl font-bold text-gray-900 dark:text-neo-text mt-1">{stat.value}</p>
                                    </div>
                                    <div className={`p-2.5 rounded-xl border ${colorClass}`}>
                                        <Icon className="w-5 h-5" />
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>

                {/* Devices Table */}
                <div className="rounded-xl bg-white dark:bg-neo-dark/60 backdrop-blur-sm border border-gray-200 dark:border-neo-primary/20 shadow-md dark:shadow-lg overflow-hidden">
                    <div className="px-5 py-4 border-b border-gray-200 dark:border-neo-primary/20">
                        <h2 className="text-lg font-semibold text-gray-900 dark:text-neo-text flex items-center gap-2">
                            <span className="w-1 h-5 bg-gradient-to-b from-neo-primary to-neo-secondary rounded-full" />
                            Network Devices
                        </h2>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-gray-50 dark:bg-primary-950/50 border-b border-gray-200 dark:border-neo-primary/20">
                                <tr>
                                    {['Device', 'Network Info', 'Activity', 'Status', 'Actions'].map((header) => (
                                        <th
                                            key={header}
                                            className="px-5 py-3 text-left text-xs font-semibold text-gray-700 dark:text-neo-dim uppercase tracking-wider"
                                        >
                                            {header}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200 dark:divide-neo-primary/10">
                                {devices.map((device) => (
                                    <tr
                                        key={device.mac}
                                        className="hover:bg-neo-primary/5 dark:hover:bg-neo-primary/5 transition-colors"
                                    >
                                        <td className="px-5 py-4 whitespace-nowrap">
                                            <div className="flex items-center gap-3">
                                                {getDeviceIcon(device.deviceType)}
                                                <div>
                                                    <div className="text-sm font-medium text-gray-900 dark:text-neo-text">
                                                        {device.hostname}
                                                    </div>
                                                    <div className="text-xs text-gray-500 dark:text-neo-dim capitalize">
                                                        {device.deviceType}
                                                    </div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-5 py-4 whitespace-nowrap">
                                            <div className="text-sm font-mono text-gray-900 dark:text-neo-text">{device.ip}</div>
                                            <div className="text-xs font-mono text-gray-500 dark:text-neo-dim">{device.mac}</div>
                                        </td>
                                        <td className="px-5 py-4 whitespace-nowrap">
                                            <div className="flex items-center gap-1 text-sm text-gray-900 dark:text-neo-text">
                                                <ClockIcon className="w-3.5 h-3.5 text-gray-400" />
                                                {device.lastSeen}
                                            </div>
                                            <div className="text-xs text-gray-500 dark:text-neo-dim">
                                                <span className="text-neo-primary">↑</span> {device.upload} •{' '}
                                                <span className="text-cyber-400">↓</span> {device.download}
                                            </div>
                                        </td>
                                        <td className="px-5 py-4 whitespace-nowrap">
                                            {device.authenticated ? (
                                                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-neo-primary/20 text-neo-primary border border-neo-primary/30">
                                                    <ShieldCheckIcon className="w-3.5 h-3.5" />
                                                    Authenticated
                                                </span>
                                            ) : (
                                                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/30">
                                                    <ShieldExclamationIcon className="w-3.5 h-3.5" />
                                                    Blocked
                                                </span>
                                            )}
                                        </td>
                                        <td className="px-5 py-4 whitespace-nowrap">
                                            {device.authenticated ? (
                                                <button
                                                    onClick={() => handleRevokeAccess(device.mac)}
                                                    disabled={loading}
                                                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-500/30 hover:bg-red-100 dark:hover:bg-red-500/20 transition-all duration-200 disabled:opacity-50"
                                                >
                                                    <XCircleIcon className="w-4 h-4" />
                                                    Revoke
                                                </button>
                                            ) : (
                                                <button
                                                    onClick={() => handleGrantAccess(device.mac)}
                                                    disabled={loading}
                                                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-neo-primary/20 text-neo-primary border border-neo-primary/30 hover:bg-neo-primary/30 transition-all duration-200 disabled:opacity-50"
                                                >
                                                    <CheckBadgeIcon className="w-4 h-4" />
                                                    Grant Access
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {devices.length === 0 && (
                        <div className="py-12 text-center">
                            <WifiIcon className="mx-auto h-10 w-10 text-neo-primary/40" />
                            <p className="mt-3 text-sm text-gray-500 dark:text-neo-dim">No devices connected</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default DevicesPage;
