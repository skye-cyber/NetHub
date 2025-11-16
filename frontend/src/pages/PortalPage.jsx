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
        <div className='container font-exo-2 h-[100vh] w-[100vw] overflow-y-auto overflow-x-hidden'>
            <title>NeoPortal Access</title>

            <div className="bg-matrix fixed top-0 left-0 size-full opacity-10 z-[-1]"></div>
            <div className="flex items-center justify-center min-h-[100vh] p-6">
                <div className="relative bg-[rgba(10, 10, 26, 0.8)] backdrop-blur-sm border border-[rgba(0, 240, 255, 0.2)] rounded-md p-8 w-full max-w-lg shadow-[0_0_100px_rgba(0,240,255,0.1),_inset_0_1px_0_rgba(255,255,255,0.1)] before:content-[''] before:absolute before:top-0 before:left-0 before:h-1 before:bg-[linear-gradient(90deg, transparent, var(--primary), transparent)]">
                    {/* Header */}
                    <div className="header flex justify-between items-center m-2">
                        <div className="logo flex items-center gap-2">
                            <div className="logo-icon text-lg animate-heartpulse">⚡</div>
                            <h1 className='font-orbitron font-semibold bg-gradient-to-br from-neo-primary to-neo-accent bg-clip-text text-transparent'>NEO<span className='bg-gradient-to-br from-neo-accent to-neo-secondary bg-clip-text text-transparent ml-1'>PORTAL</span></h1>
                        </div>
                        <div className="network-status flex items-center gap-2 text-sm text-dim">
                            <div className="status-indicator w-2 h-2 rounded-full bg-neo-primary animate-blink"></div>
                            <span className='text-neo-dim'>NETWORK READY</span>
                        </div>
                    </div>

                    {/* Welcome Section */}
                    <div className="welcome-section text-center  mb-4">
                        <h2 className='font-brand text-md mb-2 bg-gradient-to-br from-neo-text to-neo-primary bg-clip-text text-transparent'>QUANTUM NETWORK ACCESS</h2>
                        <p className='text-neo-dim leading-[1.6]'>
                            You've entered the secure gateway. Accept terms to proceed with full
                            bandwidth access.
                        </p>
                    </div>

                    {/* Device Info */}
                    <div className="device-info bg-[rgba(0, 240, 255, 0.05)] border border-[rgba(0, 240, 255, 0.1)] rounded-md p-2 mb-4">
                        <div className="info-grid grid grid-cols-[repeat(auto-fit,_minmax(150px,_1fr))] gap-2">
                            <div className="block text-sm color-neo-dim mb-0.5 uppercase tracking-tight">
                                <label>DEVICE ID</label>
                                <div className="font-mono text-sm text-neo-primary break-all">{clientInfo?.mac}</div>
                            </div>
                            <div className="block text-sm color-neo-dim mb-0.5 uppercase tracking-tight">
                                <label>IP VECTOr</label>
                                <div className="font-mono text-sm text-neo-primary break-all">{clientInfo?.ip}</div>
                            </div>
                            <div className="block text-sm color-neo-dim mb-0.5 uppercase tracking-tight">
                                <label>CONNECTION</label>
                                <div className="font-mono text-sm text-neo-primary break-all">ENCRYPTED</div>
                            </div>
                        </div>
                    </div>

                    {/* Terms */}
                    <div className="m-4">
                        <h3 className='font-brand font-md mb-4 text-neo-primary'>ACCESS PROTOCOL</h3>
                        <div className="space-y-1">
                            <div className="flex items-center gap-2 padding-x-2 border border-[rgba(255, 255, 255, 0.05)] last-child:border-b-none">
                                <div className="text-neo-primary font-bold min-w-2">✓</div>
                                <span>I agree to use this network responsibly and ethically</span>
                            </div>
                            <div className="flex items-center gap-2 padding-x-2 border border-[rgba(255, 255, 255, 0.05)] last-child:border-b-none">
                                <div className="text-neo-primary font-bold min-w-2">✓</div>
                                <span
                                >I understand network usage may be monitored for security</span
                                >
                            </div>
                            <div className="flex items-center gap-2 padding-x-2 border border-[rgba(255, 255, 255, 0.05)] last-child:border-b-none">
                                <div className="text-neo-primary font-bold min-w-2">✓</div>
                                <span>I will not engage in malicious activities</span>
                            </div>
                            <div className="flex items-center gap-2 padding-x-2 border border-[rgba(255, 255, 255, 0.05)] last-child:border-b-none">
                                <div className="text-neo-primary font-bold min-w-2">✓</div>
                                <span>I accept the bandwidth and usage policies</span>
                            </div>
                        </div>
                    </div>

                    {/* Connect Button */}
                    <div className="text-center">
                        <button id="connectBtn" className="connect-button relative overflow-hidden w-full max-w-md bg-gradient-to-br from-neo-primary to-neo-secondary border-none rounded-lg p-4 font-orbitron font-semibold  text-neo-dark cursor-pointer transition-all duration-300 ease-in-out hover:-translate-y-[2px] shadow-md shadow-x-[rgba(0, 240, 255, 0.3)] shadow-y-[rgba(123, 66, 246, 0.2)] active:translate-y-0">
                            <span className="btn-text [.connect-button.loading_&]:hidden">INITIATE CONNECTION</span>
                            <div className="btn-loader hidden gap-0.5 justify-center">
                                <div className="loader-dot w-2 h-2 rounded-full bg-neo-dark animate-bounce ease-in-out delay-[-0.32]"></div>
                                <div className="loader-dot w-2 h-2 rounded-full bg-neo-dark animate-bounce ease-in-out delay-[-0.16]"></div>
                                <div className="loader-dot w-2 h-2 rounded-full bg-neo-dark animate-bounce ease-in-out"></div>
                            </div>
                        </button>
                        <div id="message" className="message mt-3 padding-2 border-2 font-md hidden success:bg-[rgba(0, 255, 135, 0.1)] success:border success:border-[rgba(0, 255, 135, 0.3)] success:text-[#00ff87] error:bg-[rgba(255, 0, 100, 0.1)] border border-[rgba(255, 0, 100, 0.3)] error:text-[#ff0064]"></div>
                    </div>

                    {/* Footer */}
                    <div className="flex justify-between items-center mt-4 pt-3 font-md text-neo-dim">
                        <div className="security-badge flex items-center gap-2">
                            <span>🔒 QUANTUM ENCRYPTED</span>
                        </div>
                        <div className="version">v0.1.1 • NEO NETWORKS</div>
                    </div>
                </div>
            </div>

        </div>
    );
};

export default PortalPage;
