import React, { useState, useEffect } from 'react';
import {
    CreditCardIcon,
    DevicePhoneMobileIcon,
    ClockIcon,
    CheckCircleIcon,
    XCircleIcon,
    QrCodeIcon,
    LockClosedIcon,
    ShieldCheckIcon
} from '@heroicons/react/24/outline';
import {
    CheckCircleIcon as CheckCircleSolid,
    XCircleIcon as XCircleSolid
} from '@heroicons/react/24/solid';
import AlertUser from '../components/Notify/Notification';

const PaymentPage = () => {
    const [selectedPlan, setSelectedPlan] = useState(null);
    const [paymentMethod, setPaymentMethod] = useState('mpesa');
    const [phoneNumber, setPhoneNumber] = useState('');
    const [isProcessing, setIsProcessing] = useState(false);
    const [paymentStatus, setPaymentStatus] = useState(null);
    const [transactionId, setTransactionId] = useState('');
    const [queuePosition, setQueuePosition] = useState(null);
    const [paymentStats, setPaymentStats] = useState({ message: "", type: "" })

    const pricingPlans = [
        {
            id: '30min',
            name: '30 Minutes',
            duration: '30 minutes',
            price: 50,
            originalPrice: 70,
            savings: '29%',
            features: [
                'Basic internet access',
                'Standard speed (10 Mbps)',
                'Email & messaging',
                'Social media access'
            ],
            popular: false,
            color: 'from-blue-500 to-cyan-500'
        },
        {
            id: '1hour',
            name: '1 Hour',
            duration: '1 hour',
            price: 80,
            originalPrice: 100,
            savings: '20%',
            features: [
                'Enhanced internet access',
                'Fast speed (25 Mbps)',
                'Streaming music',
                'Video calls',
                'Cloud storage access'
            ],
            popular: true,
            color: 'from-purple-500 to-pink-500'
        },
        {
            id: '4hours',
            name: '4 Hours',
            duration: '4 hours',
            price: 250,
            originalPrice: 320,
            savings: '22%',
            features: [
                'Premium internet access',
                'High speed (50 Mbps)',
                'HD video streaming',
                'Online gaming',
                'Large file downloads',
                'Priority support'
            ],
            popular: false,
            color: 'from-green-500 to-emerald-500'
        },
        {
            id: '1day',
            name: '24 Hours',
            duration: '24 hours',
            price: 400,
            originalPrice: 500,
            savings: '20%',
            features: [
                'Full day access',
                'Ultra speed (100 Mbps)',
                '4K streaming',
                'Multiple devices',
                'VPN access',
                '24/7 premium support'
            ],
            popular: false,
            color: 'from-orange-500 to-red-500'
        },
        {
            id: '1week',
            name: '1 Week',
            duration: '7 days',
            price: 2000,
            originalPrice: 2800,
            savings: '29%',
            features: [
                'Weekly unlimited access',
                'Maximum speed (200 Mbps)',
                'Unlimited streaming',
                'Up to 5 devices',
                'Advanced security',
                'Ad-free experience',
                'Priority bandwidth'
            ],
            popular: false,
            color: 'from-indigo-500 to-purple-500'
        },
        {
            id: '1month',
            name: '1 Month',
            duration: '30 days',
            price: 6000,
            originalPrice: 9000,
            savings: '33%',
            features: [
                'Monthly unlimited access',
                'Gigabit speed (1 Gbps)',
                'Unlimited devices',
                'Enterprise security',
                'Dedicated support',
                'Early access to features',
                'Usage analytics'
            ],
            popular: false,
            color: 'from-teal-500 to-blue-500'
        }
    ];

    const paymentMethods = [
        {
            id: 'mpesa',
            name: 'M-Pesa',
            icon: DevicePhoneMobileIcon,
            description: 'Pay via M-Pesa mobile money',
            instructions: 'You will receive a prompt on your phone to enter your M-Pesa PIN'
        },
        {
            id: 'card',
            name: 'Credit/Debit Card',
            icon: CreditCardIcon,
            description: 'Pay using Visa, MasterCard, or American Express',
            instructions: 'Secure payment processed through our payment gateway'
        }
    ];

    const handlePlanSelect = (plan) => {
        setSelectedPlan(plan);
        setPaymentStatus(null);
        setTransactionId('');
    };

    const initiateMpesaPayment = async () => {
        if (!phoneNumber) return setPaymentStats({ message: "Phone Number is required", type: "warning" })
        const is_local_fmt = (phoneNumber.startsWith('07') || phoneNumber.startsWith('01') && phoneNumber.length === 10)
        const is_international_fmt = (phoneNumber.startsWith('+254') || phoneNumber.startsWith('254') || phoneNumber.length === 12)

        if (!is_local_fmt && !is_international_fmt) {
            setPaymentStats({ message: "Invalid Phone Number", type: "warning" })
            return;
        }

        setIsProcessing(true);
        setPaymentStatus('initiating');

        try {
            // Simulate API call to initiate M-Pesa payment
            const response = await mockMpesaApiCall(selectedPlan, phoneNumber);

            if (response.success) {
                setTransactionId(response.transactionId);
                setPaymentStatus('pending');
                setQueuePosition(response.queuePosition);

                // Simulate payment confirmation polling
                pollPaymentStatus(response.transactionId);
            } else {
                setPaymentStatus('failed');
                setIsProcessing(false);
            }
        } catch (error) {
            console.error('Payment initiation failed:', error);
            setPaymentStats({ message: "Payment initiation failed", type: "error" })
            setPaymentStatus('failed');
            setIsProcessing(false);
        }
    };

    const mockMpesaApiCall = (plan, phone) => {
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve({
                    success: true,
                    transactionId: 'MPE' + Date.now(),
                    queuePosition: Math.floor(Math.random() * 5) + 1,
                    message: `Payment request sent to ${phone}`
                });
            }, 2000);
        });
    };

    const pollPaymentStatus = (transactionId) => {
        const pollInterval = setInterval(async () => {
            try {
                // Simulate API call to check payment status
                const status = await mockStatusCheck(transactionId);

                if (status === 'completed') {
                    setPaymentStatus('completed');
                    setQueuePosition(null);
                    setIsProcessing(false);
                    clearInterval(pollInterval);
                    setPaymentStats({ message: "Payment completed", type: "success" })
                } else if (status === 'failed') {
                    setPaymentStatus('failed');
                    setQueuePosition(null);
                    setIsProcessing(false);
                    clearInterval(pollInterval);
                    setPaymentStats({ message: "Payment failed", type: "error" })
                }
                setPaymentStats({ message: "Payment in progress", type: "info" })
                // Continue polling if still pending
            } catch (error) {
                console.error('Status check failed:', error);
                clearInterval(pollInterval);
                setIsProcessing(false);
            }
        }, 3000);
    };

    const mockStatusCheck = (transactionId) => {
        // Simulate random status changes
        const statuses = ['pending', 'pending', 'pending', 'completed', 'failed'];
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve(statuses[Math.floor(Math.random() * statuses.length)]);
            }, 1000);
        });
    };

    const handlePayment = async () => {
        if (paymentMethod === 'mpesa') {
            await initiateMpesaPayment();
        } else {
            // Handle card payment
            setPaymentStatus('pending');
            setIsProcessing(true);
            // Simulate card payment processing
            setTimeout(() => {
                setPaymentStatus('completed');
                setTransactionId('CARD' + Date.now());
                setIsProcessing(false);
            }, 3000);
        }
    };

    const PricingCard = ({ plan }) => {
        const isSelected = selectedPlan?.id === plan.id;

        return (
            <div
                className={`bg-white/80 dark:bg-primary-800/80 backdrop-blur-sm rounded-2xl shadow-lg border-2 transition-all duration-300 hover:scale-105 hover:shadow-xl ${isSelected
                    ? 'border-blue-500 dark:border-blue-400 shadow-blue-200 dark:shadow-blue-900/50'
                    : 'border-white/20 dark:border-gray-700/50 hover:border-gray-300 dark:hover:border-gray-600'
                    } ${plan.popular ? 'ring-2 ring-purple-500 dark:ring-purple-400' : ''}`}
            >
                {plan.popular && (
                    <div className="bg-gradient-to-r from-purple-500 to-pink-500 text-white text-center py-2 text-sm font-semibold rounded-t-2xl">
                        MOST POPULAR
                    </div>
                )}

                <div className="p-6">
                    {/* Header */}
                    <div className="text-center mb-6">
                        <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                            {plan.name}
                        </h3>
                        <p className="text-gray-600 dark:text-gray-400 text-sm">
                            {plan.duration} of premium internet
                        </p>
                    </div>

                    {/* Price */}
                    <div className="text-center mb-6">
                        <div className="flex items-center justify-center space-x-2 mb-2">
                            <span className="text-4xl font-bold text-gray-900 dark:text-white">
                                KES {plan.price}
                            </span>
                            {plan.originalPrice && (
                                <span className="text-lg text-gray-500 dark:text-gray-400 line-through">
                                    KES {plan.originalPrice}
                                </span>
                            )}
                        </div>
                        {plan.savings && (
                            <span className="inline-block bg-green-100 dark:bg-green-500/20 text-green-700 dark:text-green-400 px-3 py-1 rounded-full text-sm font-medium">
                                Save {plan.savings}
                            </span>
                        )}
                    </div>

                    {/* Features */}
                    <ul className="space-y-3 mb-6">
                        {plan.features.map((feature, index) => (
                            <li key={index} className="flex items-center space-x-3">
                                <CheckCircleSolid className="w-5 h-5 text-green-500 flex-shrink-0" />
                                <span className="text-gray-700 dark:text-gray-300 text-sm">
                                    {feature}
                                </span>
                            </li>
                        ))}
                    </ul>

                    {/* Select Button */}
                    <button
                        onClick={() => handlePlanSelect(plan)}
                        className={`w-full py-3 px-4 rounded-xl font-semibold transition-all duration-300 ${isSelected
                            ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-lg'
                            : `bg-gradient-to-r ${plan.color} text-white hover:shadow-lg`
                            }`}
                    >
                        {isSelected ? 'Selected' : 'Select Plan'}
                    </button>
                </div>
            </div>
        );
    };

    const PaymentModal = () => {
        if (!selectedPlan) return null;

        const PaymentIcon = paymentMethods.find(method => method.id === paymentMethod)?.icon;

        return (
            <>
                <AlertUser message={paymentStats.message} type={paymentStats.type} />

                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-0.5 z-50">
                    <div className="relative bg-white/90 dark:bg-primary-800/90 backdrop-blur-sm rounded-2xl shadow-2xl max-w-md md:max-w-lg lg:max-w-xl max-h-[100%] w-full border border-white/20 dark:border-gray-700/50 overflow-y-auto">

                        {/* Header */}
                        <div className="sticky top-0 w-full z-10 bg-white dark:bg-primary-700 p-2 md:p-4 border-b border-gray-200 dark:border-gray-700">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-3">
                                    <LockClosedIcon className="w-6 h-6 text-green-500" />
                                    <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                                        Complete Payment
                                    </h2>
                                </div>
                                <button
                                    onClick={() => setSelectedPlan(null)}
                                    className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                                >
                                    <XCircleIcon className="w-6 h-6" />
                                </button>
                            </div>
                        </div>

                        {/* Plan Summary */}
                        <div className="p-2 md:p-4 border-b border-gray-200 dark:border-gray-700">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                                    {selectedPlan.name}
                                </h3>
                                <span className="txt-lg sm:text-2xl font-bold text-blue-600 dark:text-blue-400">
                                    KES {selectedPlan.price}
                                </span>
                            </div>
                            <p className="text-gray-600 dark:text-gray-400 text-sm">
                                {selectedPlan.duration} of premium internet access
                            </p>
                        </div>

                        {/* Payment Method Selection */}
                        <div className="p-2 sm:p-4 border-b border-gray-200 dark:border-gray-700">
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                                Payment Method
                            </h3>
                            <div className="block md:flex md:items-center md:gap-2 space-y-2 sm:space-y-3">
                                {paymentMethods.map(method => {
                                    const MethodIcon = method.icon;
                                    return (
                                        <label
                                            key={method.id}
                                            className={`flex md:flex-1 items-center space-x-2 md:space-x-2 p-2 md:p-4 md:max-h-24 rounded-xl border-2 cursor-pointer transition-all duration-200 ${paymentMethod === method.id
                                                ? 'border-blue-500 bg-blue-50 dark:bg-blue-500/10'
                                                : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                                                }`}
                                        >
                                            <input
                                                type="radio"
                                                name="paymentMethod"
                                                value={method.id}
                                                checked={paymentMethod === method.id}
                                                onChange={(e) => setPaymentMethod(e.target.value)}
                                                className="hidden text-blue-600 focus:ring-blue-500"
                                            />
                                            <MethodIcon className="w-5 h-5 sm:w-6 sm:h-6 text-gray-600 dark:text-gray-400" />
                                            <div className="flex-1">
                                                <div className="font-medium text-gray-900 dark:text-white">
                                                    {method.name}
                                                </div>
                                                <div className="text-sm text-gray-600 dark:text-gray-400">
                                                    {method.description}
                                                </div>
                                            </div>
                                        </label>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Payment Details */}
                        <div className="p-3 md:p-6">
                            {paymentMethod === 'mpesa' && (
                                <div className="space-y-2 md:space-y-3">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                            M-Pesa Phone Number
                                        </label>
                                        <input
                                            type="tel"
                                            placeholder="2547XXXXXXXX"
                                            value={phoneNumber}
                                            autoFocus="true"
                                            required
                                            onChange={(e) => setPhoneNumber(e.target.value)}
                                            className="w-full px-4 py-3 border border-gray-300 dark:border-blend-500 rounded-xl bg-white dark:bg-primary-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                                        />
                                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                                            Enter the M-Pesa registered phone number
                                        </p>
                                    </div>
                                </div>
                            )}

                            {paymentMethod === 'card' && (
                                <div className="space-y-2">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                            Card Number
                                        </label>
                                        <input
                                            type="text"
                                            required
                                            placeholder="1234 5678 9012 3456"
                                            className="w-full px-4 py-3 border border-gray-300 dark:border-blend-500 rounded-xl bg-white dark:bg-primary-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                        />
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                                Expiry Date
                                            </label>
                                            <input
                                                type="text"
                                                placeholder="MM/YY"
                                                required
                                                className="w-full px-4 py-3 border border-gray-300 dark:border-blend-500 rounded-xl bg-white dark:bg-primary-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                                CVV
                                            </label>
                                            <input
                                                type="text"
                                                placeholder="123"
                                                required="true"
                                                className="w-full px-4 py-3 border border-gray-300 dark:border-blend-500 rounded-xl bg-white dark:bg-primary-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                            />
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Payment Button */}
                            <button
                                onClick={handlePayment}
                                disabled={isProcessing || (paymentMethod === 'mpesa' && !phoneNumber)}
                                className="w-full bg-gradient-to-r from-green-600 to-emerald-600 text-white py-4 rounded-xl font-semibold mt-6 hover:from-green-700 hover:to-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 shadow-lg hover:shadow-xl"
                            >
                                {isProcessing ? (
                                    <div className="flex items-center justify-center space-x-2">
                                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                                        <span>Processing...</span>
                                    </div>
                                ) : (
                                    `Pay KES ${selectedPlan.price}`
                                )}
                            </button>

                            <div className="flex items-center justify-center space-x-2 mt-4 text-sm text-gray-500 dark:text-gray-400">
                                <ShieldCheckIcon className="w-4 h-4" />
                                <span>Secure payment encrypted</span>
                            </div>
                        </div>
                    </div>
                </div>
            </>
        );
    };

    const PaymentStatusModal = () => {
        if (!paymentStatus || !selectedPlan) return null;

        const getStatusContent = () => {
            switch (paymentStatus) {
                case 'initiating':
                    return {
                        icon: ClockIcon,
                        title: 'Initiating Payment',
                        message: 'Setting up your payment request...',
                        color: 'text-yellow-500'
                    };
                case 'pending':
                    return {
                        icon: ClockIcon,
                        title: 'Payment Pending',
                        message: 'Waiting for you to complete the payment on your phone',
                        color: 'text-yellow-500'
                    };
                case 'completed':
                    return {
                        icon: CheckCircleIcon,
                        title: 'Payment Successful!',
                        message: 'Your internet access has been activated',
                        color: 'text-green-500'
                    };
                case 'failed':
                    return {
                        icon: XCircleIcon,
                        title: 'Payment Failed',
                        message: 'The payment was not completed successfully',
                        color: 'text-red-500'
                    };
                default:
                    return null;
            }
        };

        const statusContent = getStatusContent();
        if (!statusContent) return null;

        const StatusIcon = statusContent.icon;

        return (
            <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
                <div className="bg-white/90 dark:bg-primary-800/90 backdrop-blur-sm rounded-2xl shadow-2xl max-w-md w-full border border-white/20 dark:border-gray-700/50">
                    <div className="p-8 text-center">
                        <StatusIcon className={`w-16 h-16 mx-auto mb-4 ${statusContent.color}`} />

                        <h2 className="text-2xl font-bold text-primary-900 dark:text-white mb-2">
                            {statusContent.title}
                        </h2>

                        <p className="text-gray-600 dark:text-gray-400 mb-6">
                            {statusContent.message}
                        </p>

                        {transactionId && (
                            <div className="bg-gray-100 dark:bg-secondary-600 shadow-none rounded-lg p-3 mb-4">
                                <div className="text-sm text-gray-600 dark:text-gray-400">Transaction ID</div>
                                <div className="font-mono text-gray-900 dark:text-white">{transactionId}</div>
                            </div>
                        )}

                        {queuePosition && paymentStatus === 'pending' && (
                            <div className="bg-blue-50 dark:bg-blue-500/10 rounded-lg p-4 mb-6">
                                <div className="flex items-center justify-center space-x-2 text-blue-700 dark:text-blue-400">
                                    <ClockIcon className="w-5 h-5" />
                                    <span className="font-semibold">
                                        Queue Position: #{queuePosition}
                                    </span>
                                </div>
                                <p className="text-sm text-blue-600 dark:text-blue-400 mt-1">
                                    Processing your payment request...
                                </p>
                            </div>
                        )}

                        {paymentStatus === 'completed' && (
                            <div className="space-y-4">
                                <div className="bg-green-50 dark:bg-green-500/10 rounded-lg p-4">
                                    <div className="text-green-700 dark:text-green-400 font-semibold">
                                        🎉 Access Activated!
                                    </div>
                                    <p className="text-sm text-green-600 dark:text-green-400 mt-1">
                                        You now have {selectedPlan.duration} of premium internet access
                                    </p>
                                </div>
                                <button
                                    onClick={() => {
                                        setSelectedPlan(null);
                                        setPaymentStatus(null);
                                    }}
                                    className="w-full bg-gradient-to-r from-blue-600 to-cyan-600 text-white py-3 rounded-xl font-semibold hover:from-blue-700 hover:to-cyan-700 transition-all duration-300"
                                >
                                    Start Browsing
                                </button>
                            </div>
                        )}

                        {paymentStatus === 'failed' && (
                            <div className="space-y-4">
                                <button
                                    onClick={() => setPaymentStatus(null)}
                                    className="w-full bg-gradient-to-r from-blue-600 to-cyan-600 text-white py-3 rounded-xl font-semibold hover:from-blue-700 hover:to-cyan-700 transition-all duration-300"
                                >
                                    Try Again
                                </button>
                                <button
                                    onClick={() => {
                                        setSelectedPlan(null);
                                        setPaymentStatus(null);
                                    }}
                                    className="w-full bg-gray-200 dark:bg-primary-600 text-gray-700 dark:text-gray-300 py-3 rounded-xl font-semibold hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                                >
                                    Choose Different Plan
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-primary-50 via-blue-50 to-cyan-50 dark:from-gray-900 dark:via-purple-900/20 dark:to-blue-900/20 p-4">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="text-center mb-12">
                    <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
                        Choose Your Internet Plan
                    </h1>
                    <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
                        Get instant access to high-speed internet with flexible pricing options
                    </p>
                </div>

                {/* Pricing Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-12">
                    {pricingPlans.map(plan => (
                        <PricingCard key={plan.id} plan={plan} />
                    ))}
                </div>

                {/* Features Section */}
                <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl shadow-lg p-8 border border-white/20 dark:border-gray-700/50">
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white text-center mb-8">
                        Why Choose Our Internet?
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        <div className="text-center">
                            <div className="w-16 h-16 bg-blue-100 dark:bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                                <ShieldCheckIcon className="w-8 h-8 text-blue-500" />
                            </div>
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                                Secure & Private
                            </h3>
                            <p className="text-gray-600 dark:text-gray-400">
                                Enterprise-grade security with encrypted connections
                            </p>
                        </div>
                        <div className="text-center">
                            <div className="w-16 h-16 bg-green-100 dark:bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                                <ClockIcon className="w-8 h-8 text-green-500" />
                            </div>
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                                Instant Activation
                            </h3>
                            <p className="text-gray-600 dark:text-gray-400">
                                Get connected immediately after payment confirmation
                            </p>
                        </div>
                        <div className="text-center">
                            <div className="w-16 h-16 bg-purple-100 dark:bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                                <DevicePhoneMobileIcon className="w-8 h-8 text-purple-500" />
                            </div>
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                                Easy M-Pesa Payments
                            </h3>
                            <p className="text-gray-600 dark:text-gray-400">
                                Quick and secure payments via M-Pesa mobile money
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Payment Modal */}
            <PaymentModal />

            {/* Payment Status Modal */}
            <PaymentStatusModal />
        </div>
    );
};

export default PaymentPage;
