import React, { useState, useEffect } from 'react';
import {
    WifiIcon,
    DevicePhoneMobileIcon,
    ClockIcon,
    ShieldCheckIcon,
    ChartBarIcon,
    ArrowPathIcon,
    SignalIcon,
    InformationCircleIcon
} from '@heroicons/react/24/outline';

const DashboardPage = () => {
    const [connectionTime, setConnectionTime] = useState('00:00:00');
    const [dataUsage, setDataUsage] = useState({ used: 2.1, total: 10 }); // GB
    const [networkStats, setNetworkStats] = useState({
        signalStrength: 85,
        downloadSpeed: 45,
        uploadSpeed: 12,
        latency: 28
    });

    useEffect(() => {
        const startTime = new Date();
        const timer = setInterval(() => {
            const now = new Date();
            const diff = Math.floor((now - startTime) / 1000);
            const hours = Math.floor(diff / 3600).toString().padStart(2, '0');
            const minutes = Math.floor((diff % 3600) / 60).toString().padStart(2, '0');
            const seconds = (diff % 60).toString().padStart(2, '0');
            setConnectionTime(`${hours}:${minutes}:${seconds}`);
        }, 1000);

        return () => clearInterval(timer);
    }, []);

    const quickActions = [
        {
            name: 'Speed Test',
            icon: SignalIcon,
            description: 'Test your connection speed',
            action: () => alert('Starting speed test...'),
            color: 'from-blue-500 to-cyan-500'
        },
        {
            name: 'Network Scan',
            icon: WifiIcon,
            description: 'Discover nearby networks',
            action: () => alert('Scanning networks...'),
            color: 'from-green-500 to-emerald-500'
        },
        {
            name: 'Data Usage',
            icon: ChartBarIcon,
            description: 'View usage statistics',
            action: () => alert('Showing data usage...'),
            color: 'from-purple-500 to-pink-500'
        },
        {
            name: 'Refresh',
            icon: ArrowPathIcon,
            description: 'Update connection info',
            action: () => window.location.reload(),
            color: 'from-orange-500 to-red-500'
        }
    ];

    const NetworkQualityIndicator = ({ strength }) => {
        const getColor = (strength) => {
            if (strength >= 80) return 'bg-green-500';
            if (strength >= 60) return 'bg-yellow-500';
            if (strength >= 40) return 'bg-orange-500';
            return 'bg-red-500';
        };

        return (
            <div className="flex items-center gap-2">
                <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                        className={`h-full ${getColor(strength)} transition-all duration-500`}
                        style={{ width: `${strength}%` }}
                    ></div>
                </div>
                <span className="text-sm font-medium text-gray-600">
                    {strength >= 80 ? 'Excellent' : strength >= 60 ? 'Good' : strength >= 40 ? 'Fair' : 'Poor'}
                </span>
            </div>
        );
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 dark:from-gray-900 dark:to-blue-900 p-4">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                        Network Dashboard
                    </h1>
                    <p className="text-gray-600 dark:text-gray-300">
                        Welcome to your personal network hub
                    </p>
                </div>

                {/* Connection Status Card */}
                <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 mb-6 border-l-4 border-green-500">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                            <div>
                                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                                    Connected & Secure
                                </h2>
                                <p className="text-gray-600 dark:text-gray-300 text-sm">
                                    Your connection is active and protected
                                </p>
                            </div>
                        </div>
                        <div className="text-right">
                            <p className="text-sm text-gray-500 dark:text-gray-400">Connection Time</p>
                            <p className="text-lg font-mono font-bold text-gray-900 dark:text-white">
                                {connectionTime}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Main Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    {/* Signal Strength */}
                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 border border-gray-100 dark:border-gray-700">
                        <div className="flex items-center justify-between mb-4">
                            <WifiIcon className="w-8 h-8 text-blue-500" />
                            <span className="text-2xl font-bold text-gray-900 dark:text-white">
                                {networkStats.signalStrength}%
                            </span>
                        </div>
                        <h3 className="text-gray-700 dark:text-gray-300 font-medium mb-2">Signal Strength</h3>
                        <NetworkQualityIndicator strength={networkStats.signalStrength} />
                    </div>

                    {/* Download Speed */}
                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 border border-gray-100 dark:border-gray-700">
                        <div className="flex items-center justify-between mb-4">
                            <ArrowPathIcon className="w-8 h-8 text-green-500" />
                            <span className="text-2xl font-bold text-gray-900 dark:text-white">
                                {networkStats.downloadSpeed} Mbps
                            </span>
                        </div>
                        <h3 className="text-gray-700 dark:text-gray-300 font-medium mb-2">Download Speed</h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Current rate</p>
                    </div>

                    {/* Data Usage */}
                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 border border-gray-100 dark:border-gray-700">
                        <div className="flex items-center justify-between mb-4">
                            <ChartBarIcon className="w-8 h-8 text-purple-500" />
                            <span className="text-2xl font-bold text-gray-900 dark:text-white">
                                {dataUsage.used} GB
                            </span>
                        </div>
                        <h3 className="text-gray-700 dark:text-gray-300 font-medium mb-2">Data Usage</h3>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                                className="bg-purple-500 h-2 rounded-full transition-all duration-500"
                                style={{ width: `${(dataUsage.used / dataUsage.total) * 100}%` }}
                            ></div>
                        </div>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                            {dataUsage.used} of {dataUsage.total} GB used
                        </p>
                    </div>

                    {/* Security Status */}
                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 border border-gray-100 dark:border-gray-700">
                        <div className="flex items-center justify-between mb-4">
                            <ShieldCheckIcon className="w-8 h-8 text-green-500" />
                            <span className="text-2xl font-bold text-gray-900 dark:text-white">
                                Protected
                            </span>
                        </div>
                        <h3 className="text-gray-700 dark:text-gray-300 font-medium mb-2">Security</h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Encrypted connection</p>
                    </div>
                </div>

                {/* Quick Actions */}
                <div className="mb-8">
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Quick Actions</h2>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        {quickActions.map((action, index) => (
                            <button
                                key={index}
                                onClick={action.action}
                                className={`bg-gradient-to-r ${action.color} text-white rounded-xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1 text-left group`}
                            >
                                <action.icon className="w-8 h-8 mb-3 group-hover:scale-110 transition-transform" />
                                <h3 className="font-semibold text-lg mb-1">{action.name}</h3>
                                <p className="text-white/80 text-sm">{action.description}</p>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Network Details */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Connection Details */}
                    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6">
                        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                            <InformationCircleIcon className="w-6 h-6 mr-2 text-blue-500" />
                            Connection Details
                        </h2>
                        <div className="space-y-3">
                            <div className="flex justify-between py-2 border-b border-gray-100 dark:border-gray-700">
                                <span className="text-gray-600 dark:text-gray-400">Network Name</span>
                                <span className="font-medium text-gray-900 dark:text-white">NetHub Premium</span>
                            </div>
                            <div className="flex justify-between py-2 border-b border-gray-100 dark:border-gray-700">
                                <span className="text-gray-600 dark:text-gray-400">IP Address</span>
                                <span className="font-mono text-gray-900 dark:text-white">192.168.1.45</span>
                            </div>
                            <div className="flex justify-between py-2 border-b border-gray-100 dark:border-gray-700">
                                <span className="text-gray-600 dark:text-gray-400">Upload Speed</span>
                                <span className="font-medium text-gray-900 dark:text-white">{networkStats.uploadSpeed} Mbps</span>
                            </div>
                            <div className="flex justify-between py-2">
                                <span className="text-gray-600 dark:text-gray-400">Latency</span>
                                <span className="font-medium text-gray-900 dark:text-white">{networkStats.latency} ms</span>
                            </div>
                        </div>
                    </div>

                    {/* Recent Activity */}
                    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6">
                        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                            Recent Activity
                        </h2>
                        <div className="space-y-3">
                            {[
                                { time: '2 min ago', action: 'Connected to network', type: 'success' },
                                { time: '5 min ago', action: 'Speed test completed', type: 'info' },
                                { time: '15 min ago', action: 'Device authenticated', type: 'success' },
                                { time: '1 hour ago', action: 'Network scan performed', type: 'info' }
                            ].map((activity, index) => (
                                <div key={index} className="flex items-center space-x-3 py-2 border-b border-gray-100 dark:border-gray-700 last:border-b-0">
                                    <div className={`w-2 h-2 rounded-full ${activity.type === 'success' ? 'bg-green-500' : 'bg-blue-500'
                                        }`}></div>
                                    <div className="flex-1">
                                        <p className="text-gray-900 dark:text-white">{activity.action}</p>
                                        <p className="text-sm text-gray-500 dark:text-gray-400">{activity.time}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DashboardPage;
