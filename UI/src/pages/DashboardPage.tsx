import { useState, useEffect } from 'react';
import {
    WifiIcon,
    ArrowDownTrayIcon,
    ArrowUpTrayIcon,
    ClockIcon,
    ShieldCheckIcon,
    ChartBarIcon,
    ArrowPathIcon,
    SignalIcon,
    InformationCircleIcon,
} from '@heroicons/react/24/outline';


const DashboardPage = () => {
    const [connectionTime, setConnectionTime] = useState('00:00:00');
    const [dataUsage, setDataUsage] = useState({ used: 2.1, total: 10 }); // GB
    const [networkStats, setNetworkStats] = useState({
        signalStrength: 85,
        downloadSpeed: 45.2,
        uploadSpeed: 12.8,
        latency: 28,
    });

    // Connection timer
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

    // Quick actions
    const quickActions = [
        { name: 'Speed Test', icon: SignalIcon, description: 'Measure bandwidth', action: () => console.log('Speed test') },
        { name: 'Network Scan', icon: WifiIcon, description: 'Discover devices', action: () => console.log('Network scan') },
        { name: 'Data Usage', icon: ChartBarIcon, description: 'View statistics', action: () => console.log('Data usage') },
        { name: 'Refresh', icon: ArrowPathIcon, description: 'Update data', action: () => window.location.reload() },
    ];

    // Signal strength indicator component
    const SignalStrengthBar = ({ value }: { value: number }) => {
        const getColor = (val: number) => {
            if (val >= 80) return 'bg-neo-primary';
            if (val >= 60) return 'bg-yellow-400';
            if (val >= 40) return 'bg-orange-400';
            return 'bg-red-400';
        };

        return (
            <div className="flex items-center gap-3">
                <div className="h-1.5 w-20 rounded-full bg-primary-200/50 dark:bg-primary-800/30">
                    <div
                        className={`h-full rounded-full transition-all duration-700 ${getColor(value)}`}
                        style={{ width: `${value}%` }}
                    />
                </div>
                <span className="text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-neo-dim">
                    {value >= 80 ? 'Excellent' : value >= 60 ? 'Good' : value >= 40 ? 'Fair' : 'Poor'}
                </span>
            </div>
        );
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 dark:from-neo-darker dark:to-neo-dark text-gray-900 dark:text-neo-text transition-colors duration-300">
            {/* Background decorative elements */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute -top-40 -right-40 h-96 w-96 rounded-full bg-neo-primary/5 blur-3xl" />
                <div className="absolute bottom-0 left-0 h-80 w-80 rounded-full bg-neo-secondary/5 blur-3xl" />
            </div>

            <div className="relative max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
                {/* Header */}
                <header className="mb-8 flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
                            <span className="bg-gradient-to-r from-neo-primary via-neo-secondary to-neo-accent bg-clip-text text-transparent">
                                net
                            </span>
                            <span className="text-gray-900 dark:text-neo-text">hub</span>
                        </h1>
                        <p className="text-gray-500 dark:text-neo-dim text-sm sm:text-base mt-1">
                            Personal network command center
                        </p>
                    </div>
                    <div className="flex items-center gap-3 px-4 py-2 rounded-full bg-white/80 dark:bg-neo-dark/50 backdrop-blur-sm border border-neo-primary/30 shadow-sm dark:shadow-none">
                        <div className="relative flex h-3 w-3">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-neo-primary opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-3 w-3 bg-neo-primary"></span>
                        </div>
                        <span className="text-sm font-medium text-gray-700 dark:text-neo-text">Live</span>
                    </div>
                </header>

                {/* Connection Status Card */}
                <div className="relative mb-8 rounded-2xl bg-gradient-to-r from-white to-white dark:from-neo-dark/80 dark:to-primary-950/80 backdrop-blur-md border border-neo-primary/20 shadow-neo-light dark:shadow-neo animate-glow-pulse-light dark:animate-glow-pulse">
                    <div className="absolute inset-0 rounded-2xl bg-neo-primary/5 dark:bg-neo-primary/5" />
                    <div className="relative p-6 flex flex-wrap items-center justify-between gap-4">
                        <div className="flex items-center gap-4">
                            <div className="p-3 rounded-xl bg-neo-primary/10 border border-neo-primary/30">
                                <ShieldCheckIcon className="w-6 h-6 text-neo-primary" />
                            </div>
                            <div>
                                <h3 className="text-lg font-semibold text-gray-900 dark:text-neo-text flex items-center gap-2">
                                    Connected & Secure
                                    <span className="text-xs px-2 py-0.5 rounded-full bg-neo-primary/20 text-neo-primary border border-neo-primary/30">
                                        WPA3
                                    </span>
                                </h3>
                                <p className="text-sm text-gray-500 dark:text-neo-dim">Your connection is encrypted and protected</p>
                            </div>
                        </div>
                        <div className="text-right">
                            <p className="text-xs uppercase tracking-wider text-gray-400 dark:text-neo-dim">Uptime</p>
                            <p className="text-2xl font-mono font-bold text-gray-900 dark:text-neo-text tabular-nums">
                                {connectionTime}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Main Stats Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-10">
                    {/* Signal Strength */}
                    <div className="group relative overflow-hidden rounded-xl bg-white dark:bg-neo-dark/60 backdrop-blur-sm border border-gray-200 dark:border-neo-primary/10 hover:border-neo-primary/40 dark:hover:border-neo-primary/30 transition-all duration-300 shadow-md dark:shadow-lg hover:shadow-lg dark:hover:shadow-neo">
                        <div className="absolute inset-0 bg-gradient-to-br from-neo-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                        <div className="relative p-5">
                            <div className="flex items-start justify-between mb-3">
                                <WifiIcon className="w-6 h-6 text-neo-primary" />
                                <span className="text-3xl font-bold text-gray-900 dark:text-neo-text">
                                    {networkStats.signalStrength}
                                    <span className="text-sm text-gray-400 dark:text-neo-dim ml-0.5">%</span>
                                </span>
                            </div>
                            <h4 className="text-sm font-medium text-gray-500 dark:text-neo-dim uppercase tracking-wider mb-2">
                                Signal Strength
                            </h4>
                            <SignalStrengthBar value={networkStats.signalStrength} />
                        </div>
                    </div>

                    {/* Download Speed */}
                    <div className="group relative overflow-hidden rounded-xl bg-white dark:bg-neo-dark/60 backdrop-blur-sm border border-gray-200 dark:border-neo-primary/10 hover:border-neo-primary/40 dark:hover:border-neo-primary/30 transition-all duration-300 shadow-md dark:shadow-lg hover:shadow-lg dark:hover:shadow-neo">
                        <div className="absolute inset-0 bg-gradient-to-br from-cyber-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                        <div className="relative p-5">
                            <div className="flex items-start justify-between mb-3">
                                <ArrowDownTrayIcon className="w-6 h-6 text-cyber-500" />
                                <span className="text-3xl font-bold text-gray-900 dark:text-neo-text">
                                    {networkStats.downloadSpeed}
                                    <span className="text-sm text-gray-400 dark:text-neo-dim ml-0.5">Mbps</span>
                                </span>
                            </div>
                            <h4 className="text-sm font-medium text-gray-500 dark:text-neo-dim uppercase tracking-wider mb-1">
                                Download
                            </h4>
                            <p className="text-xs text-gray-400 dark:text-neo-dim/70">Current throughput</p>
                        </div>
                    </div>

                    {/* Upload Speed */}
                    <div className="group relative overflow-hidden rounded-xl bg-white dark:bg-neo-dark/60 backdrop-blur-sm border border-gray-200 dark:border-neo-primary/10 hover:border-neo-primary/40 dark:hover:border-neo-primary/30 transition-all duration-300 shadow-md dark:shadow-lg hover:shadow-lg dark:hover:shadow-neo">
                        <div className="absolute inset-0 bg-gradient-to-br from-neo-secondary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                        <div className="relative p-5">
                            <div className="flex items-start justify-between mb-3">
                                <ArrowUpTrayIcon className="w-6 h-6 text-neo-secondary" />
                                <span className="text-3xl font-bold text-gray-900 dark:text-neo-text">
                                    {networkStats.uploadSpeed}
                                    <span className="text-sm text-gray-400 dark:text-neo-dim ml-0.5">Mbps</span>
                                </span>
                            </div>
                            <h4 className="text-sm font-medium text-gray-500 dark:text-neo-dim uppercase tracking-wider mb-1">
                                Upload
                            </h4>
                            <p className="text-xs text-gray-400 dark:text-neo-dim/70">Current throughput</p>
                        </div>
                    </div>

                    {/* Data Usage */}
                    <div className="group relative overflow-hidden rounded-xl bg-white dark:bg-neo-dark/60 backdrop-blur-sm border border-gray-200 dark:border-neo-primary/10 hover:border-neo-primary/40 dark:hover:border-neo-primary/30 transition-all duration-300 shadow-md dark:shadow-lg hover:shadow-lg dark:hover:shadow-neo">
                        <div className="absolute inset-0 bg-gradient-to-br from-neo-accent/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                        <div className="relative p-5">
                            <div className="flex items-start justify-between mb-3">
                                <ChartBarIcon className="w-6 h-6 text-neo-accent" />
                                <span className="text-xl font-bold text-gray-900 dark:text-neo-text">
                                    {dataUsage.used}
                                    <span className="text-sm text-gray-400 dark:text-neo-dim ml-0.5">GB</span>
                                </span>
                            </div>
                            <h4 className="text-sm font-medium text-gray-500 dark:text-neo-dim uppercase tracking-wider mb-2">
                                Data Usage
                            </h4>
                            <div className="h-1.5 w-full rounded-full bg-gray-200 dark:bg-primary-800/30">
                                <div
                                    className="h-full rounded-full bg-gradient-to-r from-neo-accent to-neo-secondary transition-all duration-700"
                                    style={{ width: `${(dataUsage.used / dataUsage.total) * 100}%` }}
                                />
                            </div>
                            <p className="text-xs text-gray-400 dark:text-neo-dim/70 mt-2">
                                {dataUsage.used} of {dataUsage.total} GB used
                            </p>
                        </div>
                    </div>
                </div>

                {/* Quick Actions */}
                <section className="mb-10">
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-neo-text mb-5 flex items-center gap-2">
                        <span className="w-1 h-5 bg-gradient-to-b from-neo-primary to-neo-secondary rounded-full" />
                        Quick Actions
                    </h2>
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                        {quickActions.map((action, idx) => (
                            <button
                                key={idx}
                                onClick={action.action}
                                className="group relative overflow-hidden rounded-xl bg-white dark:bg-neo-dark/60 backdrop-blur-sm border border-gray-200 dark:border-neo-primary/20 p-5 text-left transition-all duration-300 hover:border-neo-primary/50 hover:shadow-lg dark:hover:shadow-neo hover:-translate-y-1"
                            >
                                <div className="absolute inset-0 bg-gradient-to-br from-neo-primary/10 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                                <div className="relative">
                                    <action.icon className="w-7 h-7 mb-3 text-neo-primary group-hover:scale-110 transition-transform duration-300" />
                                    <h3 className="text-lg font-semibold text-gray-900 dark:text-neo-text">{action.name}</h3>
                                    <p className="text-xs text-gray-500 dark:text-neo-dim mt-1">{action.description}</p>
                                </div>
                            </button>
                        ))}
                    </div>
                </section>

                {/* Bottom Panels */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Connection Details */}
                    <div className="rounded-xl bg-white dark:bg-neo-dark/60 backdrop-blur-sm border border-gray-200 dark:border-neo-primary/20 p-6 shadow-md dark:shadow-lg">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-neo-text mb-4 flex items-center gap-2">
                            <InformationCircleIcon className="w-5 h-5 text-neo-primary" />
                            Connection Details
                        </h3>
                        <div className="space-y-3">
                            {[
                                { label: 'Network Name', value: 'NetHub_5G' },
                                { label: 'IP Address', value: '192.168.1.45' },
                                { label: 'Gateway', value: '192.168.1.1' },
                                { label: 'DNS', value: '1.1.1.1' },
                                { label: 'Latency', value: `${networkStats.latency} ms` },
                            ].map((item, i) => (
                                <div key={i} className="flex justify-between py-2 border-b border-gray-200 dark:border-neo-primary/10 last:border-0">
                                    <span className="text-gray-500 dark:text-neo-dim">{item.label}</span>
                                    <span className="font-mono text-sm text-gray-900 dark:text-neo-text">{item.value}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Recent Activity */}
                    <div className="rounded-xl bg-white dark:bg-neo-dark/60 backdrop-blur-sm border border-gray-200 dark:border-neo-primary/20 p-6 shadow-md dark:shadow-lg">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-neo-text mb-4">Recent Activity</h3>
                        <div className="space-y-3">
                            {[
                                { time: '2 min ago', action: 'Connected to NetHub_5G', type: 'success' },
                                { time: '5 min ago', action: 'Speed test completed', type: 'info' },
                                { time: '15 min ago', action: 'Device authenticated', type: 'success' },
                                { time: '1 hour ago', action: 'Network scan performed', type: 'info' },
                            ].map((activity, i) => (
                                <div key={i} className="flex items-center gap-3 py-2 border-b border-gray-200 dark:border-neo-primary/10 last:border-0">
                                    <div className={`h-2 w-2 rounded-full ${activity.type === 'success' ? 'bg-neo-primary' : 'bg-cyber-400'
                                        }`} />
                                    <div className="flex-1">
                                        <p className="text-gray-900 dark:text-neo-text text-sm">{activity.action}</p>
                                        <p className="text-xs text-gray-500 dark:text-neo-dim">{activity.time}</p>
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
