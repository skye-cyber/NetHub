import React, {useState, useEffect} from 'react';
import { useLocation } from 'react-router-dom';
import { Box, Typography, Container, Paper } from '@mui/material';

const DashboardPage = () => {
    const location = useLocation();
    const searchParams = new URLSearchParams(location.search);
    const clientIp = searchParams.get('ip') || 'Unknown';
    const clientMac = searchParams.get('mac') || 'Unknown';

    const [connectionTime, setConnectionTime] = useState('00:00');

    useEffect(() => {
        // Simulate connection timer
        const startTime = new Date();
        const timer = setInterval(() => {
            const now = new Date();
            const diff = Math.floor((now - startTime) / 1000);
            const minutes = Math.floor(diff / 60).toString().padStart(2, '0');
            const seconds = (diff % 60).toString().padStart(2, '0');
            setConnectionTime(`${minutes}:${seconds}`);
        }, 1000);

        return () => clearInterval(timer);
    }, []);

    const testConnection = () => {
        alert('Testing connection...');
    };

    const openSpeedTest = () => {
        alert('Opening speed test...');
    };

    const showNetworkInfo = () => {
        alert(`IP: ${clientIp}\nMAC: ${clientMac}`);
    };

    const openHelp = () => {
        alert('Opening help...');
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-400 to-purple-600 flex items-center justify-center p-5">
            <div className="bg-white/95 backdrop-blur-lg rounded-2xl shadow-xl p-8 md:p-10 w-full max-w-6xl animate-slide-up">
                {/* Header */}
                <div className="text-center mb-10">
                    <div className="text-6xl mb-6 animate-bounce">🎉</div>
                    <h1 className="text-3xl md:text-4xl font-bold text-gray-800 mb-3">
                        Welcome to Our Network!
                    </h1>
                    <p className="text-gray-600 text-lg">
                        You're now connected and ready to explore
                    </p>
                </div>

                {/* Connection Status */}
                <div className="flex items-center justify-center gap-3 mt-6 p-4 bg-green-100 text-green-800 rounded-xl font-semibold mb-8">
                    <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                    <span>Connected Successfully • Internet Access Active</span>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
                    <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-blue-500 hover:-translate-y-1 transition-transform duration-300 text-center">
                        <div className="text-3xl mb-4">📶</div>
                        <div className="text-xl font-bold text-gray-800 mb-1">Excellent</div>
                        <div className="text-gray-600 text-sm">Connection Quality</div>
                    </div>

                    <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-yellow-500 hover:-translate-y-1 transition-transform duration-300 text-center">
                        <div className="text-3xl mb-4">⚡</div>
                        <div class="stat-card">
                            <div class="stat-icon">⚡</div>
                            <div class="stat-value" id="connectionSpeed">13 Mbps</div>
                            <div class="stat-label">Current Speed</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon">🕒</div>
                            <div class="stat-value" id="connectionTime">00:00</div>
                            <div class="stat-label">Connection Time</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon">🔒</div>
                            <div class="stat-value">Secure</div>
                            <div class="stat-label">Network Status</div>
                        </div>
                    </div>

                    <div class="charts-container">
                        <div class="chart-card">
                            <h3>Bandwidth Usage</h3>
                            <canvas id="bandwidthChart"></canvas>
                        </div>
                        <div class="chart-card">
                            <h3>Connection Health</h3>
                            <canvas id="healthChart"></canvas>
                        </div>
                    </div>

                    <div class="quick-actions">
                        <button class="action-btn" onclick="testConnection()">
                            <span>🧪</span> Test Connection
                        </button>
                        <button class="action-btn" onclick="openSpeedTest()">
                            <span>🚀</span> Speed Test
                        </button>
                        <button class="action-btn secondary" onclick="showNetworkInfo()">
                            <span>ℹ️</span> Network Info
                        </button>
                        <button class="action-btn secondary" onclick="openHelp()">
                            <span>❓</span> Get Help
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DashboardPage;
