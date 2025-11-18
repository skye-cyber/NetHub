import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

import { connectToNetwork } from '../services/api';
//import '../components/CaptivePortal';

const CaptivePage = () => {
    const [clientInfo, setClientInfo] = useState({ ip: '192.168.x.x', mac: '00:00:00:00:00:00' });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const navigate = useNavigate();
    const [messageType, setMessageType] = useState('')
    const particle_colors = ["bg-yellow-400", "bg-green-400", "bg-neo-primary", "bg-sky-200", "bg-fuchsia-300"]

    // Simulate getting client info if backend is unavailable
    useEffect(() => {
        // This would normally come from backend, but we have fallbacks
        const simulatedIp = localStorage.getItem('client_ip') || '192.168.12.1';
        const simulatedMac = localStorage.getItem('client_mac') || '00:00:00:00:00:00';
        setClientInfo({ ip: simulatedIp, mac: simulatedMac });
        addFloatingParticles()
    }, []);

    const addFloatingParticles = useCallback(() => {
        const container = document.querySelector("#particles-container");
        for (let i = 0; i < 100; i++) {
            const particle = document.createElement('div')
            const bg_color = particle_colors[(Math.random() + 1 * 10).toFixed(0)] || particle_colors[2]

            particle.className = `absolute z-[20] w-1 h-1 ${bg_color} rounded-full pointer-events-none brightness-100`
            particle.style.cssText = `
            opacity: ${Math.random() * 0.3};
            animation: float ${5 + Math.random() * 10}s linear infinite;
            `;

            particle.style.left = `${Math.random() * 100}%`;
            particle.style.top = `${Math.random() * 100}%`;
            particle.style.animationDelay = `${Math.random() * 5}s`;

            container.appendChild(particle)
        }
    })

    const showMessage = useCallback((message, type) => {
        setMessageType(type)
        const messageEl = document.getElementById("message")
        messageEl.textContent = message
        messageEl.classList.add(type, 'block')
        messageEl.classList.remove('hidden')
    }, [setMessageType])

    const hideMessage = useCallback(() => {
        const messageEl = document.getElementById("message")
        messageEl.textContent = ''
        messageType ? messageEl.classList.remove(messageType) : ''
        messageEl.classList.remove('block')
        messageEl.classList.add('hidden')
    }, [messageType])

    const handleConnect = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await connectToNetwork();
            if (response.data.status === 'success') {
                navigate(response.data.redirect_url);
                showMessage("Connection successfull", "success")
            } else {
                setError(response.data.message);
            }
        } catch (err) {
            if (err.status === 'network_error') {
                setError('Server unavailable. Please check your connection or try again later.');
                showMessage("Failed to connect", "error")
                setMessageType("error")

                // Store attempt for when connection is restored
                localStorage.setItem('pending_connection', 'true');
            } else {
                setError(err.message || 'Failed to connect to the network');
            }
        } finally {
            setLoading(false);
            setTimeout(() => {
                hideMessage()
            }, 3000)
        }
    }, [setMessageType, setError]);


    return (
        <div className='min-h-screen bg-white dark:bg-primary-900 font-modern flex flex-col'>
            <title>NeoPortal Access</title>

            {/* Background Pattern */}
            <div className="bg-grid-light dark:bg-matrix fixed top-0 left-0 w-full h-full opacity-10 z-[-1]"></div>

            {/* Main Content Container */}
            <div id="particles-container" className="relative flex-1 flex items-center justify-center p-4 sm:p-6">
                <div className="relative bg-white dark:bg-[#0a0a1a]/95 backdrop-blur-sm border border-gray-200 dark:border-[#00f0ff]/20 rounded-lg p-6 sm:p-8 w-full max-w-md lg:max-w-lg shadow-lg dark:shadow-[0_0_100px_#00f0ff/10,_inset_0_1px_0_#ffffff/10] before:content-[''] before:absolute before:top-0 before:left-0 before:right-0 before:h-0.5 before:bg-gradient-to-r before:from-transparent before:via-blue-500 dark:before:via-[#00f0ff] before:to-transparent mb-20">

                    {/* Header */}
                    <div className="header flex justify-between items-center mb-4">
                        <div className="logo flex items-center gap-2">
                            <div className="logo-icon text-lg animate-heartpulse">⚡</div>
                            <h1 className='font-orbitron text-2xl font-bold tracking-tighter bg-gradient-to-br from-blue-600 to-purple-700 dark:from-[#00f0ff] dark:to-[#7b42f6] bg-clip-text text-transparent'>
                                NEO<span className='text-gray-800 dark:text-[#7944ff] ml-1'>PORTAL</span>
                            </h1>
                        </div>
                        <div className="network-status flex items-center gap-2 text-xs text-gray-500 dark:text-[#00f0ff]/70">
                            <div className="status-indicator w-2 h-2 rounded-full bg-green-500 dark:bg-[#00f0ff] animate-blink"></div>
                            <span className='hidden sm:inline text-gray-600 dark:text-[#00f0ff]/70'>NETWORK READY</span>
                        </div>
                    </div>

                    {/* Welcome Section */}
                    <div className="welcome-section text-center mb-6">
                        <h2 className='font-orbitron text-lg mb-3 bg-gradient-to-br from-gray-800 to-blue-600 dark:from-white dark:to-[#00f0ff] bg-clip-text text-transparent'>QUANTUM NETWORK ACCESS</h2>
                        <p className='text-gray-600 dark:text-gray-300 leading-relaxed text-sm'>
                            You've entered the secure gateway. Accept terms to proceed with full bandwidth access.
                        </p>
                    </div>

                    {/* Device Info */}
                    <div className="device-info bg-blue-50/50 dark:bg-[#00f0ff]/5 border border-blue-200 dark:border-[#00f0ff]/10 rounded-md p-4 mb-6">
                        <div className="info-grid grid grid-cols-1 md:grid-cols-2 gap-3">
                            <div className="block">
                                <label className='text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wide'>DEVICE ID</label>
                                <div className="font-mono text-sm text-blue-700 dark:text-[#00f0ff] break-all mt-1">{clientInfo?.mac}</div>
                            </div>
                            <div className="block">
                                <label className='text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wide'>IP VECTOR</label>
                                <div className="font-mono text-sm text-blue-700 dark:text-[#00f0ff] break-all mt-1">{clientInfo?.ip}</div>
                            </div>
                            <div className="block">
                                <label className='text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wide'>CONNECTION</label>
                                <div className="font-mono text-sm text-blue-700 dark:text-[#00f0ff] break-all mt-1">ENCRYPTED</div>
                            </div>
                        </div>
                    </div>

                    {/* Terms */}
                    <div className="mb-6">
                        <h3 className='font-orbitron text-base mb-4 text-gray-800 dark:text-[#00f0ff]'>ACCESS PROTOCOL</h3>
                        <div className="space-y-3">
                            {[
                                "I agree to use this network responsibly and ethically",
                                "I understand network usage may be monitored for security",
                                "I will not engage in malicious activities",
                                "I accept the bandwidth and usage policies"
                            ].map((term, index) => (
                                <div key={index} className="flex items-start gap-3 p-2">
                                    <div className="text-green-500 dark:text-[#00f0ff] font-bold text-sm mt-0.5 flex-shrink-0">✓</div>
                                    <span className='text-gray-700 dark:text-white/80 text-sm leading-relaxed'>{term}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Connect Button */}
                    <div className="text-center">
                        <button
                            id="connectBtn"
                            onClick={handleConnect}
                            className="connect-button relative flex justify-center gap-2 overflow-hidden w-full bg-gradient-to-r from-blue-500 to-purple-600 dark:from-[#4993dc] dark:to-[#366ba1] border-none rounded-lg py-4 font-orbitron font-semibold text-white cursor-pointer transition-all duration-300 ease-in-out hover:-translate-y-[1px] shadow-lg hover:shadow-xl dark:shadow-[0_0_30px_#00f0ff/30] active:translate-y-0"
                        >
                            <div className={`btn-loader ${loading ? 'flex' : 'hidden'} gap-1 justify-center items-center`}>
                                <div className="loader-dot w-2 h-2 rounded-full bg-white dark:bg-green-300 animate-bounce" style={{ animationDelay: '-0.32s' }}></div>
                                <div className="loader-dot w-2 h-2 rounded-full bg-white dark:bg-yellow-400 animate-bounce" style={{ animationDelay: '-0.16s' }}></div>
                                <div className="loader-dot w-2 h-2 rounded-full bg-white animate-bounce"></div>
                            </div>
                            <span className="btn-text [.connect-button.loading_&]:hidden">INITIATE CONNECTION</span>
                        </button>
                        <div id="message" className="message hidden mt-3 p-3 rounded border text-sm message:bg-green-50 successdark:bg-green-100 success:border-green-200 success:text-green-700 dark:success:bg-[#00ff87]/10 dark:success:border-[#00ff87]/30 dark:success:text-[#00ff87] error:bg-red-50 error:border-red-200 error:text-red-700 dark:error:bg-[#ff0064]/10 dark:error:border-[#ff0064]/30 dark:error:text-[#ff0064]"> Network error</div>
                    </div>

                    {/* Footer */}
                    <div className="flex flex-col sm:flex-row justify-between items-center gap-2 mt-6 pt-4 text-xs text-gray-500 dark:text-[#00f0ff]/70 border-t border-gray-200 dark:border-[#00f0ff]/10">
                        <div className="security-badge flex items-center gap-2">
                            <span>🔒 QUANTUM ENCRYPTED</span>
                        </div>
                        <div className="version text-center sm:text-right">v0.1.1 • NEO NETWORKS</div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CaptivePage;
