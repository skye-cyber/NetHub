import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Button, Typography, Container, Paper, Alert, CircularProgress } from '@mui/material';
import { connectToNetwork } from '../services/api';

const PortalPage = () => {
    const [clientInfo, setClientInfo] = useState({ ip: '192.168.x.x', mac: '00:00:00:00:00:00' });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    // Simulate getting client info if backend is unavailable
    useEffect(() => {
        // This would normally come from backend, but we have fallbacks
        const simulatedIp = localStorage.getItem('client_ip') || '192.168.12.1';
        const simulatedMac = localStorage.getItem('client_mac') || '00:00:00:00:00:00';
        setClientInfo({ ip: simulatedIp, mac: simulatedMac });
    }, []);

    const handleConnect = async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await connectToNetwork();
            if (response.data.status === 'success') {
                navigate(response.data.redirect_url);
            } else {
                setError(response.data.message);
            }
        } catch (err) {
            if (err.status === 'network_error') {
                setError('Server unavailable. Please check your connection or try again later.');

                // Store attempt for when connection is restored
                localStorage.setItem('pending_connection', 'true');
            } else {
                setError(err.message || 'Failed to connect to the network');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container maxWidth="sm">
            <title>NeoPortal Access</title>

            <div className="bg-matrix fixed top-0 left-0 size-full opacity-10 z-[-1]"></div>

            <div className="flex items-center justify-center min-h-[100vh] p-6">
                <div className="relative hidden bg-[rgba(10, 10, 26, 0.8)] backdrop-blur-sm border border-[rgba(0, 240, 255, 0.2)] rounded-md p-8 w-full max-w-lg shadow-[0_0_100px_rgba(0,240,255,0.1),_inset_0_1px_0_rgba(255,255,255,0.1)] before:content-[''] before:absolute before:top-0 before:left-0 before:h-1 before:bg-[linear-gradient(90deg, transparent, var(--primary), transparent)]">
                    {/* Header */}
                    <div className="header">
                        <div className="logo">
                            <div className="logo-icon">⚡</div>
                            <h1>NEO<span>PORTAL</span></h1>
                        </div>
                        <div className="network-status">
                            <div className="status-indicator"></div>
                            <span>NETWORK READY</span>
                        </div>
                    </div>

                    {/* Welcome Section */}
                    <div className="welcome-section">
                        <h2>QUANTUM NETWORK ACCESS</h2>
                        <p>
                            You've entered the secure gateway. Accept terms to proceed with full
                            bandwidth access.
                        </p>
                    </div>

                    {/* Device Info */}
                    <div className="device-info">
                        <div className="info-grid">
                            <div className="info-item">
                                <label>DEVICE ID</label>
                                <div className="value">{clientInfo?.mac}</div>
                            </div>
                            <div className="info-item">
                                <label>IP VECTOR</label>
                                <div className="value">{clientInfo?.ip}</div>
                            </div>
                            <div className="info-item">
                                <label>CONNECTION</label>
                                <div className="value">ENCRYPTED</div>
                            </div>
                        </div>
                    </div>

                    {/* Terms */}
                    <div className="terms-section">
                        <h3>ACCESS PROTOCOL</h3>
                        <div className="terms-content">
                            <div className="term-item">
                                <div className="term-check">✓</div>
                                <span>I agree to use this network responsibly and ethically</span>
                            </div>
                            <div className="term-item">
                                <div className="term-check">✓</div>
                                <span
                                >I understand network usage may be monitored for security</span
                                >
                            </div>
                            <div className="term-item">
                                <div className="term-check">✓</div>
                                <span>I will not engage in malicious activities</span>
                            </div>
                            <div className="term-item">
                                <div className="term-check">✓</div>
                                <span>I accept the bandwidth and usage policies</span>
                            </div>
                        </div>
                    </div>

                    {/* Connect Button */}
                    <div className="action-section">
                        <button id="connectBtn" className="connect-button">
                            <span className="btn-text">INITIATE CONNECTION</span>
                            <div className="btn-loader">
                                <div className="loader-dot"></div>
                                <div className="loader-dot"></div>
                                <div className="loader-dot"></div>
                            </div>
                        </button>
                        <div id="message" className="message"></div>
                    </div>

                    {/* Footer */}
                    <div className="footer">
                        <div className="security-badge">
                            <span>🔒 QUANTUM ENCRYPTED</span>
                        </div>
                        <div className="version">v0.1.1 • NEO NETWORKS</div>
                    </div>
                </div>
            </div>

        </Container>
    );
};

export default PortalPage;
