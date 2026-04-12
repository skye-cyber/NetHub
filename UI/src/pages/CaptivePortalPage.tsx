import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { connectToNetwork, deviceInfor } from '../services/api';
import { ShieldCheckIcon, LockClosedIcon, BoltIcon } from '@heroicons/react/24/outline';

const CaptivePage = () => {
    const [clientInfo, setClientInfo] = useState({
        ip: localStorage.getItem('client_ip') || '',
        mac: localStorage.getItem('client_mac') || '',
    });
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState({ text: '', type: '' });
    const navigate = useNavigate();

    useEffect(() => {
        if (!clientInfo.ip || !clientInfo.mac) {
            fetchClientInfo();
        }
    }, []);

    const fetchClientInfo = async () => {
        try {
            const response = await deviceInfor();
            if (response.status === 200) {
                setClientInfo(response.data);
                localStorage.setItem('client_ip', response.data.client_ip);
                localStorage.setItem('client_mac', response.data.client_mac);
            }
        } catch (error) {
            console.error('Failed to fetch device info:', error);
        }
    };

    const handleConnect = async () => {
        setLoading(true);
        setMessage({ text: '', type: '' });

        try {
            const response = await connectToNetwork();
            if (response.data.status === '200') {
                setMessage({ text: 'Connection successful! Redirecting...', type: 'success' });
                setTimeout(() => navigate(response.data.redirect_url), 1500);
            } else {
                setMessage({ text: response.data.message || 'Connection failed', type: 'error' });
            }
        } catch (err) {
            setMessage({
                text: err.message || 'Network error. Please try again.',
                type: 'error',
            });
        } finally {
            setLoading(false);
        }
    };

    const terms = [
        'I agree to use this network responsibly and ethically',
        'I understand network usage may be monitored for security',
        'I will not engage in malicious activities',
        'I accept the bandwidth and usage policies',
    ];

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 dark:from-neo-darker dark:to-neo-dark transition-colors duration-300 flex items-center justify-center p-4">
            {/* Ambient glows */}
            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute -top-40 -right-40 h-96 w-96 rounded-full bg-neo-primary/5 blur-3xl" />
                <div className="absolute bottom-0 left-0 h-80 w-80 rounded-full bg-neo-secondary/5 blur-3xl" />
            </div>

            <div className="relative w-full max-w-lg">
                {/* Main Card */}
                <div className="rounded-2xl bg-white dark:bg-neo-dark/80 backdrop-blur-md border border-gray-200 dark:border-neo-primary/20 shadow-neo-light dark:shadow-neo overflow-hidden">
                    {/* Top accent line */}
                    <div className="h-1 bg-gradient-to-r from-neo-primary via-neo-secondary to-neo-accent" />

                    <div className="p-6 sm:p-8">
                        {/* Header */}
                        <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center gap-2">
                                <BoltIcon className="w-6 h-6 text-neo-primary" />
                                <h1 className="text-2xl font-bold tracking-tight">
                                    <span className="bg-gradient-to-r from-neo-primary to-neo-secondary bg-clip-text text-transparent">
                                        Captive
                                    </span>
                                    <span className="text-gray-900 dark:text-neo-text">Portal</span>
                                </h1>
                            </div>
                            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-neo-primary/10 border border-neo-primary/30">
                                <span className="relative flex h-2 w-2">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-neo-primary opacity-75" />
                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-neo-primary" />
                                </span>
                                <span className="text-xs font-medium text-neo-primary">LIVE</span>
                            </div>
                        </div>

                        {/* Welcome */}
                        <div className="mb-6">
                            <h2 className="text-lg font-semibold text-gray-900 dark:text-neo-text mb-2">
                                Secure Network Access
                            </h2>
                            <p className="text-sm text-gray-500 dark:text-neo-dim leading-relaxed">
                                You've connected to a secure gateway. Accept the terms below to gain full access.
                            </p>
                        </div>

                        {/* Device Info Card */}
                        <div className="rounded-xl bg-gray-50 dark:bg-primary-950/50 border border-gray-200 dark:border-neo-primary/20 p-4 mb-6">
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div>
                                    <p className="text-xs font-medium text-gray-500 dark:text-neo-dim uppercase tracking-wider mb-1">
                                        Device ID
                                    </p>
                                    <p className="font-mono text-sm text-gray-900 dark:text-neo-text break-all">
                                        {clientInfo.mac || '—'}
                                    </p>
                                </div>
                                <div>
                                    <p className="text-xs font-medium text-gray-500 dark:text-neo-dim uppercase tracking-wider mb-1">
                                        IP Address
                                    </p>
                                    <p className="font-mono text-sm text-gray-900 dark:text-neo-text break-all">
                                        {clientInfo.ip || '—'}
                                    </p>
                                </div>
                                <div className="sm:col-span-2 flex items-center gap-2">
                                    <LockClosedIcon className="w-4 h-4 text-neo-primary" />
                                    <span className="text-xs font-medium text-neo-primary uppercase tracking-wider">
                                        Connection Encrypted
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* Terms */}
                        <div className="mb-8">
                            <h3 className="text-sm font-semibold text-gray-900 dark:text-neo-text mb-3 flex items-center gap-2">
                                <ShieldCheckIcon className="w-4 h-4 text-neo-primary" />
                                Access Protocol
                            </h3>
                            <ul className="space-y-2">
                                {terms.map((term, idx) => (
                                    <li key={idx} className="flex items-start gap-3">
                                        <span className="text-neo-primary text-sm mt-0.5">✓</span>
                                        <span className="text-sm text-gray-600 dark:text-neo-dim">{term}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>

                        {/* Connect Button */}
                        <button
                            onClick={handleConnect}
                            disabled={loading}
                            className="relative w-full py-3.5 rounded-xl bg-gradient-to-r from-neo-primary to-cyber-500 text-white dark:text-gray-900 font-semibold text-sm uppercase tracking-wider shadow-md hover:shadow-neo transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed overflow-hidden group"
                        >
                            {loading ? (
                                <div className="flex items-center justify-center gap-1.5">
                                    <span className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                    <span className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                    <span className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                </div>
                            ) : (
                                'Initiate Connection'
                            )}
                        </button>

                        {/* Message */}
                        {message.text && (
                            <div
                                className={`mt-4 p-3 rounded-lg text-sm ${message.type === 'success'
                                        ? 'bg-neo-primary/10 border border-neo-primary/30 text-neo-primary'
                                        : 'bg-red-500/10 border border-red-500/30 text-red-600 dark:text-red-400'
                                    }`}
                            >
                                {message.text}
                            </div>
                        )}

                        {/* Footer */}
                        <div className="flex flex-wrap items-center justify-between gap-3 mt-6 pt-4 border-t border-gray-200 dark:border-neo-primary/20">
                            <div className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-neo-dim">
                                <LockClosedIcon className="w-3.5 h-3.5" />
                                <span>Quantum Encrypted</span>
                            </div>
                            <div className="text-xs text-gray-400 dark:text-neo-dim/70">
                                v0.1.1 • NetHub Networks
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CaptivePage;
