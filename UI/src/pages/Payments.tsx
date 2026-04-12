import React, { useState } from 'react';
import {
    DevicePhoneMobileIcon,
    CreditCardIcon,
    ClockIcon,
    CheckCircleIcon,
    XCircleIcon,
    ShieldCheckIcon,
    LockClosedIcon,
    XMarkIcon,
} from '@heroicons/react/24/outline';
import { CheckCircleIcon as CheckCircleSolid } from '@heroicons/react/24/solid';

const PaymentPage = () => {
    const [selectedPlan, setSelectedPlan] = useState(null);
    const [paymentMethod, setPaymentMethod] = useState('mpesa');
    const [phoneNumber, setPhoneNumber] = useState('');
    const [isProcessing, setIsProcessing] = useState(false);
    const [paymentStatus, setPaymentStatus] = useState(null);
    const [transactionId, setTransactionId] = useState('');

    const pricingPlans = [
        {
            id: '1hour',
            name: '1 Hour',
            price: 10,
            features: ['5 Mbps', 'Streaming', 'Video calls'],
            color: 'from-neo-primary to-cyber-500',
        },
        {
            id: '1day',
            name: '24 Hours',
            price: 60,
            features: ['10 Mbps', '4K streaming', 'Multiple devices'],
            color: 'from-neo-secondary to-neo-accent',
        },
        {
            id: '1week',
            name: '1 Week',
            price: 250,
            features: ['15 Mbps', 'Unlimited devices', 'Priority support'],
            color: 'from-cyber-500 to-neo-primary',
        },
        {
            id: '1month',
            name: '1 Month',
            price: 600,
            features: ['Gigabit', 'Enterprise security', 'Dedicated support'],
            color: 'from-neo-accent to-neo-secondary',
        },
    ];

    const paymentMethods = [
        { id: 'mpesa', name: 'M-Pesa', icon: DevicePhoneMobileIcon },
        { id: 'card', name: 'Card', icon: CreditCardIcon },
    ];

    const handlePlanSelect = (plan) => {
        setSelectedPlan(plan);
        setPaymentStatus(null);
    };

    const handlePayment = async () => {
        if (paymentMethod === 'mpesa' && !phoneNumber) return;
        setIsProcessing(true);
        setPaymentStatus('processing');

        // Simulate payment
        setTimeout(() => {
            const success = Math.random() > 0.2;
            if (success) {
                setPaymentStatus('success');
                setTransactionId(`TXN${Date.now()}`);
            } else {
                setPaymentStatus('failed');
            }
            setIsProcessing(false);
        }, 2000);
    };

    const closeModal = () => {
        setSelectedPlan(null);
        setPaymentStatus(null);
        setPhoneNumber('');
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 dark:from-neo-darker dark:to-neo-dark p-4 sm:p-6 transition-colors duration-300">
            {/* Ambient glows */}
            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute -top-40 -right-40 h-96 w-96 rounded-full bg-neo-primary/5 blur-3xl" />
                <div className="absolute bottom-0 left-0 h-80 w-80 rounded-full bg-neo-secondary/5 blur-3xl" />
            </div>

            <div className="relative max-w-6xl mx-auto">
                <div className="text-center mb-10">
                    <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
                        <span className="bg-gradient-to-r from-neo-primary via-neo-secondary to-neo-accent bg-clip-text text-transparent">
                            Choose
                        </span>
                        <span className="text-gray-900 dark:text-neo-text"> Your Plan</span>
                    </h1>
                    <p className="text-gray-500 dark:text-neo-dim text-sm sm:text-base mt-2">
                        Instant high-speed internet access
                    </p>
                </div>

                {/* Pricing Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {pricingPlans.map((plan) => (
                        <div
                            key={plan.id}
                            onClick={() => handlePlanSelect(plan)}
                            className={`group relative overflow-hidden rounded-xl bg-white dark:bg-neo-dark/60 backdrop-blur-sm border cursor-pointer transition-all duration-300 ${selectedPlan?.id === plan.id
                                    ? 'border-neo-primary shadow-neo dark:shadow-neo'
                                    : 'border-gray-200 dark:border-neo-primary/20 hover:border-neo-primary/40 shadow-md dark:shadow-lg'
                                }`}
                        >
                            <div className="p-5">
                                <h3 className="text-lg font-semibold text-gray-900 dark:text-neo-text mb-1">{plan.name}</h3>
                                <div className="flex items-baseline gap-1 mb-3">
                                    <span className="text-2xl font-bold text-gray-900 dark:text-neo-text">Ksh {plan.price}</span>
                                </div>
                                <ul className="space-y-2 mb-4">
                                    {plan.features.map((feature, i) => (
                                        <li key={i} className="flex items-center gap-2 text-sm text-gray-600 dark:text-neo-dim">
                                            <CheckCircleSolid className="w-4 h-4 text-neo-primary flex-shrink-0" />
                                            {feature}
                                        </li>
                                    ))}
                                </ul>
                                <div className={`h-1 w-full rounded-full bg-gradient-to-r ${plan.color} opacity-50 group-hover:opacity-100 transition-opacity`} />
                            </div>
                        </div>
                    ))}
                </div>

                {/* Trust badges */}
                <div className="flex flex-wrap items-center justify-center gap-6 mt-10 text-sm text-gray-500 dark:text-neo-dim">
                    <div className="flex items-center gap-1.5">
                        <ShieldCheckIcon className="w-4 h-4 text-neo-primary" />
                        <span>Secure & Encrypted</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                        <ClockIcon className="w-4 h-4 text-neo-primary" />
                        <span>Instant Activation</span>
                    </div>
                </div>
            </div>

            {/* Payment Modal */}
            {selectedPlan && !paymentStatus && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
                    <div className="relative w-full max-w-md rounded-xl bg-white dark:bg-neo-dark/90 backdrop-blur-md border border-gray-200 dark:border-neo-primary/30 shadow-neo-light dark:shadow-neo">
                        <div className="h-1 bg-gradient-to-r from-neo-primary to-neo-secondary rounded-t-xl" />
                        <div className="p-5">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-lg font-semibold text-gray-900 dark:text-neo-text">Payment Details</h2>
                                <button onClick={closeModal} className="text-gray-400 hover:text-gray-600 dark:hover:text-neo-dim">
                                    <XMarkIcon className="w-5 h-5" />
                                </button>
                            </div>

                            <div className="mb-4 p-3 rounded-lg bg-gray-50 dark:bg-primary-950/50 border border-gray-200 dark:border-neo-primary/20">
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-gray-600 dark:text-neo-dim">{selectedPlan.name}</span>
                                    <span className="font-semibold text-gray-900 dark:text-neo-text">Ksh {selectedPlan.price}</span>
                                </div>
                            </div>

                            <div className="mb-4">
                                <label className="block text-sm font-medium text-gray-700 dark:text-neo-dim mb-2">Payment Method</label>
                                <div className="flex gap-2">
                                    {paymentMethods.map((method) => {
                                        const Icon = method.icon;
                                        return (
                                            <button
                                                key={method.id}
                                                onClick={() => setPaymentMethod(method.id)}
                                                className={`flex-1 flex items-center justify-center gap-2 p-2.5 rounded-lg border text-sm transition-all ${paymentMethod === method.id
                                                        ? 'border-neo-primary bg-neo-primary/10 text-neo-primary'
                                                        : 'border-gray-200 dark:border-neo-primary/20 text-gray-600 dark:text-neo-dim hover:bg-gray-50 dark:hover:bg-primary-900/50'
                                                    }`}
                                            >
                                                <Icon className="w-4 h-4" />
                                                {method.name}
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>

                            {paymentMethod === 'mpesa' && (
                                <div className="mb-5">
                                    <label className="block text-sm font-medium text-gray-700 dark:text-neo-dim mb-1">M-Pesa Number</label>
                                    <input
                                        type="tel"
                                        placeholder="0712 345 678"
                                        value={phoneNumber}
                                        onChange={(e) => setPhoneNumber(e.target.value)}
                                        className="w-full px-4 py-2.5 rounded-lg bg-gray-50 dark:bg-primary-950/50 border border-gray-200 dark:border-neo-primary/20 text-gray-900 dark:text-neo-text focus:border-neo-primary focus:ring-1 focus:ring-neo-primary/30 outline-none"
                                    />
                                </div>
                            )}

                            {paymentMethod === 'card' && (
                                <div className="space-y-3 mb-5">
                                    <input
                                        placeholder="Card Number"
                                        className="w-full px-4 py-2.5 rounded-lg bg-gray-50 dark:bg-primary-950/50 border border-gray-200 dark:border-neo-primary/20"
                                    />
                                    <div className="grid grid-cols-2 gap-2">
                                        <input placeholder="MM/YY" className="px-4 py-2.5 rounded-lg bg-gray-50 dark:bg-primary-950/50 border border-gray-200 dark:border-neo-primary/20" />
                                        <input placeholder="CVV" className="px-4 py-2.5 rounded-lg bg-gray-50 dark:bg-primary-950/50 border border-gray-200 dark:border-neo-primary/20" />
                                    </div>
                                </div>
                            )}

                            <button
                                onClick={handlePayment}
                                disabled={isProcessing || (paymentMethod === 'mpesa' && !phoneNumber)}
                                className="w-full py-3 rounded-xl bg-gradient-to-r from-neo-primary to-cyber-500 text-white dark:text-gray-900 font-medium shadow-md hover:shadow-neo transition-all duration-300 disabled:opacity-50"
                            >
                                {isProcessing ? 'Processing...' : `Pay Ksh ${selectedPlan.price}`}
                            </button>

                            <p className="flex items-center justify-center gap-1.5 mt-3 text-xs text-gray-500 dark:text-neo-dim">
                                <LockClosedIcon className="w-3.5 h-3.5" />
                                Secure payment
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Payment Status Modal */}
            {paymentStatus && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
                    <div className="w-full max-w-sm rounded-xl bg-white dark:bg-neo-dark/90 backdrop-blur-md border border-gray-200 dark:border-neo-primary/30 p-6 text-center shadow-neo-light dark:shadow-neo">
                        {paymentStatus === 'processing' && (
                            <>
                                <div className="animate-spin rounded-full h-10 w-10 border-2 border-neo-primary border-t-transparent mx-auto mb-4" />
                                <h3 className="text-lg font-semibold text-gray-900 dark:text-neo-text mb-1">Processing Payment</h3>
                                <p className="text-sm text-gray-500 dark:text-neo-dim">Please wait...</p>
                            </>
                        )}
                        {paymentStatus === 'success' && (
                            <>
                                <CheckCircleIcon className="w-12 h-12 text-neo-primary mx-auto mb-4" />
                                <h3 className="text-lg font-semibold text-gray-900 dark:text-neo-text mb-1">Payment Successful!</h3>
                                <p className="text-sm text-gray-500 dark:text-neo-dim mb-2">Your internet access is now active.</p>
                                <p className="text-xs font-mono text-neo-dim mb-4">TXN: {transactionId}</p>
                                <button
                                    onClick={closeModal}
                                    className="w-full py-2.5 rounded-lg bg-gradient-to-r from-neo-primary to-cyber-500 text-white dark:text-gray-900 font-medium"
                                >
                                    Start Browsing
                                </button>
                            </>
                        )}
                        {paymentStatus === 'failed' && (
                            <>
                                <XCircleIcon className="w-12 h-12 text-red-500 mx-auto mb-4" />
                                <h3 className="text-lg font-semibold text-gray-900 dark:text-neo-text mb-1">Payment Failed</h3>
                                <p className="text-sm text-gray-500 dark:text-neo-dim mb-4">Please try again.</p>
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => setPaymentStatus(null)}
                                        className="flex-1 py-2.5 rounded-lg bg-neo-primary/20 text-neo-primary border border-neo-primary/30 font-medium"
                                    >
                                        Retry
                                    </button>
                                    <button
                                        onClick={closeModal}
                                        className="flex-1 py-2.5 rounded-lg bg-gray-100 dark:bg-primary-900/50 text-gray-700 dark:text-neo-dim font-medium"
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default PaymentPage;
